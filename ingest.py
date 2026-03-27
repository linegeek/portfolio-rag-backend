import os

from config import QDRANT_COLLECTION
from app.services import load_text_file, ingest_documents

if __name__ == "__main__":
    filenames = []

    docs = []

    for filename in filenames:
        file_path = os.path.join("data", filename)
        file_text = load_text_file(file_path)
        docs.append(
            {
                "source": filename,
                "text": file_text,
            }
        )

    count = ingest_documents(docs)
    print(f"Ingested {count} chunks into Qdrant collection '{QDRANT_COLLECTION}'")

