# RAG App

A Retrieval-Augmented Generation (RAG) API that answers questions grounded in your own documents. It embeds documents into a vector store, semantically retrieves relevant chunks at query time, and feeds them as context to a large language model to produce cited, factual answers.

---

## About This Project

RAG App is a backend service that combines semantic search with LLM-based answer generation. Instead of relying solely on a model's training data, every answer is anchored to documents you provide — reducing hallucinations and giving full traceability through source citations.

Key capabilities:
- **Document ingestion** — load plain-text files, split them into overlapping chunks, embed them, and store them in a vector database.
- **Semantic retrieval** — encode a user query and perform cosine-similarity search over the vector store to surface the most relevant chunks.
- **Grounded generation** — pass retrieved chunks as context to an LLM, which produces an answer and cites its sources (`[Source 1]`, `[Source 2]`, …).
- **Conversation history** — the `/ask` endpoint accepts a message history so the model can handle follow-up questions coherently.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| LLM | [Anthropic Claude](https://www.anthropic.com/) (`claude-haiku-4-5`) |
| Vector database | [Qdrant](https://qdrant.tech/) |
| Embedding model | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) via `sentence-transformers` |
| Data validation | [Pydantic](https://docs.pydantic.dev/) |
| Config management | `python-dotenv` |
| Language | Python 3.11+ |

---

## Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          Client                                 │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTP
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI  (app.py)                           │
│                                                                 │
│   POST /ask        POST /retrieve        GET /health            │
└────────┬───────────────────┬─────────────────────────────────────┘
         │                   │
         ▼                   ▼
┌─────────────────┐  ┌──────────────────────────────────────────┐
│   llm.py        │  │              retrieve.py                 │
│                 │  │                                          │
│  Anthropic      │  │  SentenceTransformer  →  Qdrant          │
│  Claude API     │  │  (embed query)           (vector search) │
└────────▲────────┘  └──────────────────────────────────────────┘
         │ context chunks
         └──────────────────────────────────────────────────────┘

Ingestion pipeline (run once / on new documents):

  data/*.txt  →  ingest.py  →  chunk_text()  →  embed_texts()  →  Qdrant
```

### Module overview

| File | Responsibility |
|---|---|
| `app.py` | FastAPI application, request/response models, endpoint handlers |
| `ingest.py` | Document loading, chunking, embedding, and upserting into Qdrant |
| `retrieve.py` | Query embedding and vector similarity search against Qdrant |
| `llm.py` | Prompt construction and answer generation via Anthropic Claude |
| `config.py` | Centralised configuration loaded from environment variables |
| `utils.py` | Shared helpers (content extraction, text normalisation) |

### API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status": "ok"}` |
| `POST` | `/ask` | Full RAG pipeline: retrieves context and returns a cited answer |
| `POST` | `/retrieve` | Returns raw retrieved chunks without calling the LLM |

---

## How to Run the Project

### Prerequisites

- Python 3.11+
- [Docker](https://www.docker.com/) (to run Qdrant locally)
- An [Anthropic API key](https://console.anthropic.com/)

### 1 — Clone and set up the environment

```bash
git clone <repo-url>
cd rag_app

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2 — Configure environment variables

Create a `.env` file in the project root:

```env
ANTHROPIC_API_KEY=sk-ant-...

# Optional — defaults shown
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=rag_docs
EMBED_MODEL=all-MiniLM-L6-v2
CLAUDE_MODEL=claude-haiku-4-5-20251001
TOP_K=5
MAX_HISTORY_MESSAGES=10
```

### 3 — Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4 — Ingest documents

Place plain-text files in the `data/` directory, then run:

```bash
python ingest.py
```

This chunks each file, embeds the chunks, and upserts them into the Qdrant collection.

### 5 — Start the API server

```bash
uvicorn app:app --reload
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Example request

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {
        "role": "user",
        "parts": [{ "type": "text", "text": "How many days can employees work remotely?" }]
      }
    ]
  }'
```

---

## References

- [Ollama](https://ollama.com/) — run large language models locally; can be used as an alternative LLM backend
- [Llama 3.2 3B](https://ollama.com/library/llama3.2) — compact open-weight model available via Ollama (`ollama pull llama3.2:3b`)
- [Hugging Face](https://huggingface.co/) — model hub used to source the `all-MiniLM-L6-v2` embedding model via `sentence-transformers`
- [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) — lightweight, high-quality sentence embedding model
- [Qdrant](https://qdrant.tech/) — open-source vector database for storing and querying embeddings
- [Anthropic Claude](https://www.anthropic.com/) — LLM used for grounded answer generation
- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework for building APIs
