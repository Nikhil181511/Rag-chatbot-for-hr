import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Computed,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("document_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    parent_section: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    sheet_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    row_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    row_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_ocr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    chunk_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    embedding: Mapped[List[float]] = mapped_column(Vector(1536), nullable=False)
    tsvector_content: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', content)", persisted=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    document_version: Mapped["DocumentVersion"] = relationship(
        "DocumentVersion", back_populates="chunks"
    )

    __table_args__ = (
        Index("ix_chunks_tsvector", "tsvector_content", postgresql_using="gin"),
        Index("uq_version_chunk_index", "document_version_id", "chunk_index", unique=True),
    )
