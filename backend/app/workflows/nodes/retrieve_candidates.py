import time
from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.config.database import async_session_factory
from app.retrieval.hybrid_retriever import HybridRetriever


async def retrieve_candidates_node(state: RAGState) -> Dict[str, Any]:
    query = state.get("original_query", "")
    filters = state.get("filters", {})
    from app.config.langfuse import active_observation_ctx
    lf_root = active_observation_ctx.get() or state.get("_lf_root")

    span = None
    if lf_root:
        try:
            span = lf_root.start_observation(
                name="retrieve_and_rerank",
                input={"query": query, "filters": filters},
            )
        except Exception:
            pass

    t0 = time.time()
    async with async_session_factory() as session:
        retriever = HybridRetriever(session)
        results = await retriever.retrieve(query=query, filters=filters)
    retrieval_duration = round(time.time() - t0, 3)

    retrieved = results.get("dense", []) + results.get("sparse", [])

    if span:
        try:
            span.update(
                output={
                    "retrieved_count": len(retrieved),
                    "dense_count": len(results.get("dense", [])),
                    "sparse_count": len(results.get("sparse", [])),
                },
                metadata={"latency_sec": retrieval_duration},
            )
            span.end()
        except Exception:
            pass

    existing_durations = dict(state.get("node_durations") or {})
    existing_durations["retrieve_candidates"] = retrieval_duration

    return {
        "retrieved_candidates": [
            {
                "chunk_id": str(c.chunk_id),
                "document_id": str(c.document_id),
                "document_name": c.document_name,
                "content": c.content,
                "score": c.score,
                "page_number": c.page_number,
                "section": c.section,
                "sheet_name": c.sheet_name,
                "row_start": c.row_start,
                "row_end": c.row_end,
                "source": c.source,
                "metadata": c.metadata,
            }
            for c in (results.get("dense", []) + results.get("sparse", []))
        ],
        "_raw_dense": results.get("dense", []),
        "_raw_sparse": results.get("sparse", []),
    }
