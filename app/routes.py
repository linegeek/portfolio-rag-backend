from fastapi import APIRouter, HTTPException

from config import TOP_K
from app.schemas import AskRequest, AskResponse, SourceItem, RetrieveResponse, ContextItem
from app.services import (
    extract_latest_user_question,
    retrieve_context,
)

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/retrieve", response_model=RetrieveResponse)
def retrieve(req: AskRequest) -> RetrieveResponse:
    if not req.messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    question = extract_latest_user_question(req.messages)
    if not question:
        raise HTTPException(status_code=400, detail="Could not extract user question")

    top_k = req.top_k or TOP_K
    contexts = retrieve_context(req.collection, question, top_k=top_k)

    return RetrieveResponse(
        question=question,
        contexts=[
            ContextItem(
                text=item["text"],
                source=item["source"],
                chunk_index=item["chunk_index"],
                score=float(item["score"]),
            )
            for item in contexts
        ],
    )

