import uuid
from typing import Optional, List, Dict, Any, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.rag_run import RAGRun


class RAGRunRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, run_id: uuid.UUID) -> Optional[RAGRun]:
        stmt = select(RAGRun).where(RAGRun.id == run_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_request_id(self, request_id: str) -> Optional[RAGRun]:
        stmt = select(RAGRun).where(RAGRun.request_id == request_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_conversation(
        self, conversation_id: uuid.UUID, limit: int = 50
    ) -> Sequence[RAGRun]:
        stmt = (
            select(RAGRun)
            .where(RAGRun.conversation_id == conversation_id)
            .order_by(RAGRun.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_rag_run(
        self,
        conversation_id: uuid.UUID,
        request_id: str,
        trace_id: str,
        query: str,
        rewritten_queries: Optional[List[str]] = None,
        intent: Optional[str] = None,
        domain: Optional[str] = None,
        retrieval_mode: Optional[str] = None,
        reranker: Optional[str] = None,
        retrieved_chunk_ids: Optional[List[uuid.UUID]] = None,
        selected_chunk_ids: Optional[List[uuid.UUID]] = None,
        retrieval_scores: Optional[Dict[str, Any]] = None,
        context_token_count: int = 0,
        llm_model: str = "gpt-4o-mini",
        input_token_count: int = 0,
        output_token_count: int = 0,
        generation_latency_ms: int = 0,
        total_latency_ms: int = 0,
        citation_validation_result: Optional[str] = None,
        groundedness_result: Optional[str] = None,
        guardrail_result: Optional[str] = None,
        retry_count: int = 0,
        final_answer_status: str = "SUCCESS",
        error_detail: Optional[str] = None,
    ) -> RAGRun:
        run = RAGRun(
            conversation_id=conversation_id,
            request_id=request_id,
            trace_id=trace_id,
            query=query,
            rewritten_queries=rewritten_queries or [],
            intent=intent,
            domain=domain,
            retrieval_mode=retrieval_mode,
            reranker=reranker,
            retrieved_chunk_ids=retrieved_chunk_ids or [],
            selected_chunk_ids=selected_chunk_ids or [],
            retrieval_scores=retrieval_scores or {},
            context_token_count=context_token_count,
            llm_model=llm_model,
            input_token_count=input_token_count,
            output_token_count=output_token_count,
            generation_latency_ms=generation_latency_ms,
            total_latency_ms=total_latency_ms,
            citation_validation_result=citation_validation_result,
            groundedness_result=groundedness_result,
            guardrail_result=guardrail_result,
            retry_count=retry_count,
            final_answer_status=final_answer_status,
            error_detail=error_detail,
        )
        self.session.add(run)
        await self.session.flush()
        return run
