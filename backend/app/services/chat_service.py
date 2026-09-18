import asyncio
import json
import time
import uuid
from typing import AsyncGenerator, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows.rag_graph import rag_app
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.rag_run_repository import RAGRunRepository
from app.schemas.chat import ChatRequest, ChatResponse, Citation
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)

# Active cancellation flags
_active_cancellations: Dict[str, bool] = {}


class ChatService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.conv_repo = ConversationRepository(session)
        self.rag_run_repo = RAGRunRepository(session)

    @classmethod
    def cancel_stream(cls, request_id: str) -> bool:
        if request_id in _active_cancellations:
            _active_cancellations[request_id] = True
            return True
        return False

    async def execute_chat(self, req: ChatRequest) -> ChatResponse:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())

        # 1. Get or create conversation
        conversation = await self.conv_repo.get_or_create(
            conversation_id=req.conversation_id,
            title=req.query[:60] if not req.conversation_id else None,
        )

        # 2. Fetch recent conversation history
        history_msgs = await self.conv_repo.get_messages_window(conversation.id, limit=20)
        formatted_history = [
            {"role": m.role, "content": m.content} for m in history_msgs
        ]

        # 3. Save User message to DB
        await self.conv_repo.add_message(
            conversation_id=conversation.id,
            role="user",
            content=req.query,
        )

        # 4. Invoke LangGraph RAG Workflow
        initial_state = {
            "conversation_id": conversation.id,
            "request_id": request_id,
            "trace_id": trace_id,
            "original_query": req.query,
            "conversation_history": formatted_history,
        }

        from app.config.langfuse import get_langfuse
        lf = get_langfuse()
        lf_root = None
        if lf:
            try:
                lf_root = lf.start_observation(
                    name="hr-rag-chat",
                    input={"query": req.query, "history_len": len(formatted_history)},
                    metadata={
                        "request_id": request_id,
                        "session_id": str(conversation.id),
                        "llm_model": settings.LLM_MODEL,
                        "reranker": req.reranker or settings.RERANKER_PROVIDER,
                        "embedding_model": settings.EMBEDDING_MODEL,
                    },
                )
            except Exception as e:
                logger.warning("Langfuse trace creation failed", error=str(e))

        final_state = await rag_app.ainvoke(initial_state)

        total_latency_ms = int((time.time() - start_time) * 1000)
        answer = final_state.get("final_answer", "")
        status_val = final_state.get("final_answer_status", "SUCCESS")
        is_abstention = (status_val == "ABSTENTION")
        citations_data = final_state.get("citations", [])

        # Send trace output to Langfuse
        if lf_root:
            try:
                # Log retrieval span
                retrieved = final_state.get("retrieved_candidates", [])
                selected = final_state.get("selected_context", [])
                retrieval_span = lf_root.start_observation(
                    name="retrieve_and_rerank",
                    input={"query": req.query, "filters": final_state.get("filters", {})},
                    metadata={"retrieval_quality": final_state.get("retrieval_quality", "sufficient")},
                )
                retrieval_span.update(
                    output={
                        "retrieved_count": len(retrieved),
                        "selected_count": len(selected),
                        "selected_docs": [c.get("document_name") for c in selected],
                    }
                )
                retrieval_span.end()

                # Log LLM generation
                prompt_tok = final_state.get("prompt_tokens", 0)
                comp_tok = final_state.get("completion_tokens", 0)
                tot_tok = final_state.get("total_tokens", prompt_tok + comp_tok)

                gen_span = lf_root.start_observation(
                    name="generate_draft_answer",
                    input={"query": req.query, "context_chunks": len(selected)},
                    metadata={
                        "model": settings.LLM_MODEL,
                        "groundedness": final_state.get("groundedness_result"),
                        "usage": {
                            "prompt_tokens": prompt_tok,
                            "completion_tokens": comp_tok,
                            "total_tokens": tot_tok,
                        },
                    },
                )
                gen_span.update(
                    output=final_state.get("draft_answer", ""),
                    metadata={
                        "prompt_tokens": prompt_tok,
                        "completion_tokens": comp_tok,
                        "total_tokens": tot_tok,
                    },
                )
                gen_span.end()

                # Update root trace
                lf_root.update(
                    output={
                        "answer": answer,
                        "citations_count": len(citations_data),
                        "status": status_val,
                        "intent": final_state.get("intent"),
                        "groundedness": final_state.get("groundedness_result"),
                        "guardrail": final_state.get("guardrail_result"),
                        "tokens": {
                            "prompt_tokens": prompt_tok,
                            "completion_tokens": comp_tok,
                            "total_tokens": tot_tok,
                        },
                    },
                )
                lf_root.end()
                lf.flush()
            except Exception as e:
                logger.warning("Failed to record Langfuse span", error=str(e))

        # 5. Persist RAG Run record
        rag_run = await self.rag_run_repo.create_rag_run(
            conversation_id=conversation.id,
            request_id=request_id,
            trace_id=trace_id,
            query=req.query,
            rewritten_queries=final_state.get("rewritten_queries", []),
            intent=final_state.get("intent"),
            domain=final_state.get("domain"),
            retrieval_mode="hybrid_rrf",
            reranker=settings.RERANKER_PROVIDER,
            retrieved_chunk_ids=[uuid.UUID(str(c["chunk_id"])) for c in final_state.get("retrieved_candidates", []) if "chunk_id" in c],
            selected_chunk_ids=[uuid.UUID(str(c["chunk_id"])) for c in final_state.get("selected_context", []) if "chunk_id" in c],
            context_token_count=sum(c.get("token_count", 0) for c in final_state.get("selected_context", [])),
            llm_model=settings.LLM_MODEL,
            total_latency_ms=total_latency_ms,
            groundedness_result=final_state.get("groundedness_result"),
            guardrail_result=final_state.get("guardrail_result"),
            final_answer_status=status_val,
        )

        # 6. Save Assistant message to DB
        await self.conv_repo.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=answer,
            rag_run_id=rag_run.id,
            citations=citations_data,
        )

        # 7. Convert citations to response schema
        citations: list[Citation] = []
        for c in citations_data:
            citations.append(
                Citation(
                    document_id=uuid.UUID(str(c["document_id"])),
                    chunk_id=uuid.UUID(str(c["chunk_id"])),
                    document_name=c["document_name"],
                    page_number=c.get("page_number"),
                    section=c.get("section"),
                    sheet_name=c.get("sheet_name"),
                    row_start=c.get("row_start"),
                    row_end=c.get("row_end"),
                    excerpt=c.get("excerpt", ""),
                )
            )

        return ChatResponse(
            request_id=uuid.UUID(request_id),
            conversation_id=conversation.id,
            answer=answer,
            citations=citations,
            is_abstention=is_abstention,
            groundedness=final_state.get("groundedness_result", "grounded"),
            latency_ms=total_latency_ms,
        )

    async def stream_chat(self, req: ChatRequest) -> AsyncGenerator[str, None]:
        start_time = time.time()
        request_id = str(uuid.uuid4())
        trace_id = str(uuid.uuid4())
        _active_cancellations[request_id] = False

        try:
            # 1. Get or create conversation
            conversation = await self.conv_repo.get_or_create(
                conversation_id=req.conversation_id,
                title=req.query[:60] if not req.conversation_id else None,
            )

            # 2. Fetch recent conversation history
            history_msgs = await self.conv_repo.get_messages_window(conversation.id, limit=20)
            formatted_history = [
                {"role": m.role, "content": m.content} for m in history_msgs
            ]

            # 3. Save User message to DB
            await self.conv_repo.add_message(
                conversation_id=conversation.id,
                role="user",
                content=req.query,
            )

            # 4. Invoke LangGraph RAG Workflow
            initial_state = {
                "conversation_id": conversation.id,
                "request_id": request_id,
                "trace_id": trace_id,
                "original_query": req.query,
                "conversation_history": formatted_history,
            }

            from app.config.langfuse import get_langfuse
            lf = get_langfuse()
            lf_root = None
            if lf:
                try:
                    lf_root = lf.start_observation(
                        name="hr-rag-chat-stream",
                        input={"query": req.query, "history_len": len(formatted_history)},
                        metadata={
                            "request_id": request_id,
                            "session_id": str(conversation.id),
                            "llm_model": settings.LLM_MODEL,
                            "reranker": req.reranker or settings.RERANKER_PROVIDER,
                            "embedding_model": settings.EMBEDDING_MODEL,
                            "stream": True,
                        },
                    )
                except Exception as e:
                    logger.warning("Langfuse stream trace creation failed", error=str(e))

            final_state = await rag_app.ainvoke(initial_state)

            if _active_cancellations.get(request_id):
                return

            status_val = final_state.get("final_answer_status", "SUCCESS")
            answer = final_state.get("final_answer", "")
            citations_data = final_state.get("citations", [])

            if lf_root:
                try:
                    retrieved = final_state.get("retrieved_candidates", [])
                    selected = final_state.get("selected_context", [])
                    retrieval_span = lf_root.start_observation(
                        name="retrieve_and_rerank",
                        input={"query": req.query, "filters": final_state.get("filters", {})},
                        metadata={"retrieval_quality": final_state.get("retrieval_quality", "sufficient")},
                    )
                    retrieval_span.update(
                        output={
                            "retrieved_count": len(retrieved),
                            "selected_count": len(selected),
                            "selected_docs": [c.get("document_name") for c in selected],
                        }
                    )
                    retrieval_span.end()

                    prompt_tok = final_state.get("prompt_tokens", 0)
                    comp_tok = final_state.get("completion_tokens", 0)
                    tot_tok = final_state.get("total_tokens", prompt_tok + comp_tok)

                    gen_span = lf_root.start_observation(
                        name="generate_draft_answer",
                        input={"query": req.query, "context_chunks": len(selected)},
                        metadata={
                            "model": settings.LLM_MODEL,
                            "groundedness": final_state.get("groundedness_result"),
                            "usage": {
                                "prompt_tokens": prompt_tok,
                                "completion_tokens": comp_tok,
                                "total_tokens": tot_tok,
                            },
                        },
                    )
                    gen_span.update(
                        output=final_state.get("draft_answer", ""),
                        metadata={
                            "prompt_tokens": prompt_tok,
                            "completion_tokens": comp_tok,
                            "total_tokens": tot_tok,
                        },
                    )
                    gen_span.end()

                    lf_root.update(
                        output={
                            "answer": answer,
                            "citations_count": len(citations_data),
                            "status": status_val,
                            "intent": final_state.get("intent"),
                            "groundedness": final_state.get("groundedness_result"),
                            "guardrail": final_state.get("guardrail_result"),
                            "tokens": {
                                "prompt_tokens": prompt_tok,
                                "completion_tokens": comp_tok,
                                "total_tokens": tot_tok,
                            },
                        },
                    )
                    lf_root.end()
                    lf.flush()
                except Exception as e:
                    logger.warning("Failed to record Langfuse stream span", error=str(e))

            if status_val == "ABSTENTION":
                yield f"data: {json.dumps({'type': 'abstention', 'request_id': request_id, 'message': answer, 'reason': 'insufficient_context'})}\n\n"
            else:
                # Stream answer tokens (split words for natural chunking)
                words = answer.split(" ")
                for i, word in enumerate(words):
                    if _active_cancellations.get(request_id):
                        return
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield f"data: {json.dumps({'type': 'token', 'content': chunk, 'request_id': request_id})}\n\n"
                    await asyncio.sleep(0.015)

                # Emit citations event
                yield f"data: {json.dumps({'type': 'citations', 'request_id': request_id, 'citations': citations_data})}\n\n"

                total_latency = int((time.time() - start_time) * 1000)
                # Emit done event
                yield f"data: {json.dumps({'type': 'done', 'request_id': request_id, 'total_latency_ms': total_latency})}\n\n"

            # 5. Persist RAG Run record and Assistant message
            total_latency_ms = int((time.time() - start_time) * 1000)
            rag_run = await self.rag_run_repo.create_rag_run(
                conversation_id=conversation.id,
                request_id=request_id,
                trace_id=trace_id,
                query=req.query,
                rewritten_queries=final_state.get("rewritten_queries", []),
                intent=final_state.get("intent"),
                domain=final_state.get("domain"),
                retrieval_mode="hybrid_rrf",
                reranker=settings.RERANKER_PROVIDER,
                retrieved_chunk_ids=[uuid.UUID(str(c["chunk_id"])) for c in final_state.get("retrieved_candidates", []) if "chunk_id" in c],
                selected_chunk_ids=[uuid.UUID(str(c["chunk_id"])) for c in final_state.get("selected_context", []) if "chunk_id" in c],
                context_token_count=sum(c.get("token_count", 0) for c in final_state.get("selected_context", [])),
                llm_model=settings.LLM_MODEL,
                total_latency_ms=total_latency_ms,
                groundedness_result=final_state.get("groundedness_result"),
                guardrail_result=final_state.get("guardrail_result"),
                final_answer_status=status_val,
            )

            await self.conv_repo.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=answer,
                rag_run_id=rag_run.id,
                citations=citations_data,
            )

        except Exception as e:
            logger.error("Error during streaming chat", exc_info=e)
            yield f"data: {json.dumps({'type': 'error', 'request_id': request_id, 'message': 'An error occurred while generating the answer.', 'code': 'INTERNAL_ERROR'})}\n\n"
        finally:
            _active_cancellations.pop(request_id, None)
