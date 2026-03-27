import os

from config import QDRANT_COLLECTION
from app.services import load_text_file, ingest_documents

if __name__ == "__main__":
    sample_path = os.path.join("data", "sample_docs.txt")
    sample_text = load_text_file(sample_path)

    docs = [
        {
            "source": "sample_docs.txt",
            "text": sample_text,
        }
    ]

    count = ingest_documents(docs)
    print(f"Ingested {count} chunks into Qdrant collection '{QDRANT_COLLECTION}'")

