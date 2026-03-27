import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "rag_docs")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-haiku-4-5-20251001")
TOP_K = int(os.getenv("TOP_K", 5))
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "10"))
