import uuid
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    excerpt: str


class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    query: str = Field(..., min_length=1, max_length=2000)
    reranker: Optional[Literal["bge", "cohere", "none"]] = None


class ChatResponse(BaseModel):
    request_id: uuid.UUID
    conversation_id: uuid.UUID
    answer: str
    citations: List[Citation] = Field(default_factory=list)
    is_abstention: bool = False
    groundedness: str = "grounded"
    latency_ms: int = 0
