# Portfolio RAG Backend

A Retrieval-Augmented Generation (RAG) API backend built to answer questions about a personal portfolio — resume, work history, skills, and education — by semantically searching embedded documents and returning cited, grounded answers.

---

## About This Project

This is a FastAPI backend service that powers a portfolio Q&A experience. Documents (plain-text resume sections) are embedded into a Qdrant vector store. At query time the service encodes the user's question, retrieves the most relevant document chunks, and (once the LLM integration is complete) will feed those chunks to Anthropic Claude to produce a cited answer.

Key capabilities:
- **Document ingestion** — load plain-text files, split them into semantically coherent chunks via `RecursiveCharacterTextSplitter`, embed them with a sentence-transformer model, and upsert into Qdrant in batches.
- **Semantic retrieval** — encode a user query and perform cosine-similarity search over the vector store to surface the most relevant chunks.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| Vector database | [Qdrant](https://qdrant.tech/) |
| Embedding model | [all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) via `sentence-transformers` |
| Text splitting | [LangChain `RecursiveCharacterTextSplitter`](https://python.langchain.com/docs/modules/data_connection/document_transformers/) |
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
│               FastAPI  (app/__init__.py + routes.py)            │
│                                                                 │
│   POST /retrieve             GET /health                        │
└───────────────────┬─────────────────────────────────────────────┘
                    │
                    ▼
     ┌──────────────────────────────────────────┐
     │           app/services.py                │
     │                                          │
     │  SentenceTransformer  →  Qdrant          │
     │  (embed query)           (vector search) │
     │                                          │
     └──────────────────────────────────────────┘

Ingestion pipeline (run once / on new documents):

  data/*.txt  →  ingest.py  →  splitter.split_text()  →  embed_texts()  →  Qdrant
```

### Module overview

| File | Responsibility |
|---|---|
| `app/__init__.py` | FastAPI application factory |
| `app/routes.py` | Endpoint handlers (`/health`, `/retrieve`) |
| `app/services.py` | Embedding, retrieval, ingestion, and LLM prompt scaffolding |
| `app/schemas.py` | Pydantic request/response models |
| `app/utils.py` | Shared helpers (multi-format text content extraction) |
| `ingest.py` | CLI script — loads text files and calls `ingest_documents()` |
| `run.py` | Launches the Uvicorn development server |
| `config.py` | Centralised configuration loaded from environment variables |

### API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Liveness check — returns `{"status": "ok"}` |
| `POST` | `/retrieve` | Returns raw retrieved chunks without calling the LLM |

---

## How to Run the Project

### Prerequisites

- Python 3.11+
- [Docker](https://www.docker.com/) (to run Qdrant locally)

### 1 — Clone and set up the environment

```bash
git clone <repo-url>
cd portfolio-backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2 — Configure environment variables

Create a `.env` file in the project root:

```env
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=rag_docs
EMBED_MODEL=all-MiniLM-L6-v2
TOP_K=5
MAX_HISTORY_MESSAGES=10
```

### 3 — Start Qdrant

```bash
docker run -p 6333:6333 qdrant/qdrant
```

### 4 — Ingest documents

Plain-text files are already included under `data/`. To ingest them, open `ingest.py` and populate the `filenames` list with the files you want to load, then run:

```python
# ingest.py
filenames = ["info.txt", "summary.txt", "skills.txt", "education.txt"]
```

```bash
python ingest.py
```

This splits each file into overlapping chunks using `RecursiveCharacterTextSplitter`, embeds them in batches, and upserts them into the configured Qdrant collection.

### 5 — Start the API server

```bash
# Option A — via run.py
python run.py

# Option B — directly with Uvicorn
uvicorn app:app --reload
```

The API is now available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

### Example request

```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{
    "collection": "rag_docs",
    "messages": [
      {
        "role": "user",
        "parts": [{ "type": "text", "text": "What programming languages do you know?" }]
      }
    ]
  }'
```

---

## References

- [Hugging Face](https://huggingface.co/) — model hub used to source the `all-MiniLM-L6-v2` embedding model via `sentence-transformers`
- [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) — lightweight, high-quality sentence embedding model
- [Qdrant](https://qdrant.tech/) — open-source vector database for storing and querying embeddings
- [LangChain Text Splitters](https://python.langchain.com/docs/modules/data_connection/document_transformers/) — `RecursiveCharacterTextSplitter` used for semantic chunking
- [FastAPI](https://fastapi.tiangolo.com/) — modern Python web framework for building APIs
