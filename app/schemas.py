from typing import Optional, List

from pydantic import BaseModel, Field


class ChatPart(BaseModel):
    type: str
    text: Optional[str] = None


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str
    parts: Optional[List[ChatPart]] = None


class AskRequest(BaseModel):
    messages: List[ChatMessage]
    collection: str
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class SourceItem(BaseModel):
    source: str
    chunk_index: int
    score: float


class AskResponse(BaseModel):
    answer: str
    question: str
    sources: List[SourceItem]


class ContextItem(BaseModel):
    text: str
    source: str
    chunk_index: int
    score: float


class RetrieveResponse(BaseModel):
    question: str
    contexts: List[ContextItem]

