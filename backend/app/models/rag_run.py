import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import (
    String,
    Integer,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class RAGRun(Base):
    __tablename__ = "rag_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    request_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_queries: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    domain: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    retrieval_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    reranker: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    retrieved_chunk_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    selected_chunk_ids: Mapped[List[uuid.UUID]] = mapped_column(
        ARRAY(UUID(as_uuid=True)), nullable=False, default=list
    )
    retrieval_scores: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    context_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_model: Mapped[str] = mapped_column(String(64), nullable=False, default="gpt-4o-mini")
    input_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    generation_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citation_validation_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    groundedness_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    guardrail_result: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    final_answer_status: Mapped[str] = mapped_column(String(32), nullable=False, default="SUCCESS")
    error_detail: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    conversation: Mapped["Conversation"] = relationship("Conversation", back_populates="rag_runs")
