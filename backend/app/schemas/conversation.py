import uuid
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class MessageItem(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    rag_run_id: Optional[uuid.UUID] = None
    citations: Optional[List[Dict[str, Any]]] = None
    created_at: datetime


class ConversationItem(BaseModel):
    id: uuid.UUID
    title: str
    message_count: int
    updated_at: datetime


class ConversationDetailResponse(BaseModel):
    id: uuid.UUID
    title: str
    messages: List[MessageItem]


class ConversationListResponse(BaseModel):
    conversations: List[ConversationItem]


class ConversationCreateResponse(BaseModel):
    id: uuid.UUID
    title: Optional[str] = None
    created_at: datetime
