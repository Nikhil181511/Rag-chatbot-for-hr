import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from app.models.document import DocumentStatus


class DocumentItem(BaseModel):
    id: uuid.UUID
    file_name: str
    file_type: str
    file_size: int
    status: DocumentStatus
    title: Optional[str] = None
    document_category: Optional[str] = None
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentUploadItem(BaseModel):
    id: uuid.UUID
    file_name: str
    status: DocumentStatus
    file_size: int


class DocumentUploadResponse(BaseModel):
    documents: List[DocumentUploadItem]


class DocumentListResponse(BaseModel):
    documents: List[DocumentItem]
    total: int


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: DocumentStatus
    error_message: Optional[str] = None
    updated_at: datetime


class KnowledgeBaseStats(BaseModel):
    document_count: int
    ready_count: int
    failed_count: int
    total_chunks: int
    last_indexed_at: Optional[datetime] = None
