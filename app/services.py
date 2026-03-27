import uuid
from typing import Any, List, Dict

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    MAX_HISTORY_MESSAGES,
    EMBED_MODEL,
    QDRANT_URL,
    QDRANT_COLLECTION,
)
from app.schemas import ChatMessage

# ---------------------------------------------------------------------------
# Clients (initialised once at import time)
# ---------------------------------------------------------------------------

embedder = SentenceTransformer(EMBED_MODEL)
qdrant = QdrantClient(url=QDRANT_URL)

# ---------------------------------------------------------------------------
# Message / history helpers
# ---------------------------------------------------------------------------

def normalize_history(messages: List[ChatMessage]) -> List[dict]:
    normalized = []

    for message in messages:
        if message.role not in {"user", "assistant"}:
            continue

        if not message.parts:
            continue

        text = "\n".join(
            part.text or ""
            for part in message.parts
            if part.type == "text"
        ).strip()

        if not text:
            continue

        normalized.append({"role": message.role, "content": text})

    return normalized


def extract_latest_user_question(messages: List[ChatMessage]) -> str:
    for message in reversed(messages):
        if message.role != "user":
            continue

        if not message.parts:
            continue

        text = "\n".join(
            part.text or ""
            for part in message.parts
            if part.type == "text"
        ).strip()

        if text:
            return text

    return ""


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def build_context_block(contexts: List[Dict]) -> str:
    if not contexts:
        return "No relevant context was retrieved."

    blocks: List[str] = []
    for i, c in enumerate(contexts, start=1):
        blocks.append(
            f"[Source {i}] file={c['source']} chunk={c['chunk_index']}\n{c['text']}"
        )

    return "\n\n".join(blocks)


def build_messages_for_anthropic(
        question: str,
        contexts: List[Dict],
        history: List[Dict] | None = None,
) -> List[Dict]:
    context_block = build_context_block(contexts)
    messages: List[Dict] = (history or [])[-MAX_HISTORY_MESSAGES:]

    rag_user_message = f"""Use the retrieved context below to answer the user's latest question.

Retrieved context:
{context_block}

Latest user question:
{question}

Rules:
- Answer using the retrieved context when possible.
- If the context is insufficient, say you do not have enough information.
- Do not invent facts.
- Cite sources like [Source 1], [Source 2].
"""
    messages.append({"role": "user", "content": rag_user_message})
    return messages


def generate_answer(
        question: str,
        contexts: List[Dict],
        history: List[Dict] | None = None,
) -> str:
    system_prompt = (
        "You are a retrieval-agumented assistant. "
        "Use the retrieved context and recent conversation history to answer the question. "
        "Prefer the retrieved context over assumptions. "
        "If the answer is not supported by the context, clearly say you do not have enough information. "
        "Always cite sources like [Source 1], [Source 2] when using context."
    )

    messages = build_messages_for_anthropic(
        question=question,
        contexts=contexts,
        history=history,
    )

    # TODO: call ollama api


# ---------------------------------------------------------------------------
# Retrieval helpers
# ---------------------------------------------------------------------------

def embed_query(query: str) -> List[float]:
    vector = embedder.encode([query], normalize_embeddings=True)[0]
    return vector.tolist()


def retrieve_context(query: str, top_k: int = 5) -> List[Dict]:
    query_vector = embed_query(query)

    results = qdrant.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
    ).points

    contexts: List[Dict] = []
    for item in results:
        payload = item.payload or {}
        contexts.append(
            {
                "text": payload.get("text", ""),
                "source": payload.get("source", "unknown"),
                "chunk_index": payload.get("chunk_index", -1),
                "score": item.score,
            }
        )

    return contexts


# ---------------------------------------------------------------------------
# Ingestion helpers
# ---------------------------------------------------------------------------

def chunk_text(text: str, chunk_size: int = 700, overlap: int = 120) -> List[str]:
    text = text.strip()
    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def ensure_collection() -> None:
    vector_size = len(embedder.encode(["test"])[0])
    collections = qdrant.get_collections().collections
    collection_names = {c.name for c in collections}

    if QDRANT_COLLECTION not in collection_names:
        qdrant.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )


def embed_texts(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    return embedder.encode(texts, normalize_embeddings=True).tolist()


def load_text_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


# Initialize the splitter once, outside the loop
# chunk_size is in characters, but it respects word boundaries
splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""] # It tries to split by paragraph, then line, then space
)


def ingest_documents(docs: List[Dict[str, str]]) -> int:
    ensure_collection()

    points: List[PointStruct] = []
    count = 0

    for doc in docs:
        source = doc["source"]
        text = doc["text"]

        # 1. Improved Chunking: No more split words!
        chunks = splitter.split_text(text) 
        if not chunks:
            continue

        # 2. Batch Embedding (More efficient than 1-by-1)
        vectors = embed_texts(chunks)

        for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
            points.append(
                PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "text": chunk,
                        "source": source,
                        "chunk_index": idx,
                    },
                )
            )

            # 3. Memory Management: Upsert in batches of 100
            if len(points) >= 100:
                qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
                count += len(points)
                points = []

    # Final upsert for remaining points
    if points:
        qdrant.upsert(collection_name=QDRANT_COLLECTION, points=points)
        count += len(points)

    return count

