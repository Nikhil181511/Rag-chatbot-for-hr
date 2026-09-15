import uuid
from typing import Dict, Any
from app.workflows.graph_state import RAGState
from app.retrieval.context_selector import ContextSelector
from app.retrieval.reranker import ChunkCandidate


async def select_context_node(state: RAGState) -> Dict[str, Any]:
    raw_reranked = state.get("_raw_reranked") or []
    
    if not raw_reranked:
        candidates = state.get("reranked_candidates", []) or state.get("fused_candidates", [])
        raw_reranked = [
            ChunkCandidate(
                chunk_id=uuid.UUID(str(c["chunk_id"])),
                document_id=uuid.UUID(str(c["document_id"])),
                document_name=c["document_name"],
                content=c["content"],
                score=float(c["score"]),
                page_number=c.get("page_number"),
                section=c.get("section"),
                sheet_name=c.get("sheet_name"),
                row_start=c.get("row_start"),
                row_end=c.get("row_end"),
                source=c.get("source", "reranked"),
                metadata=c.get("metadata", {}),
            )
            for c in candidates
        ]
    
    if not raw_reranked:
        return {
            "selected_context": [],
            "retrieval_quality": "empty",
        }

    selector = ContextSelector()
    selected_context = selector.select(raw_reranked)

    quality = "sufficient" if selected_context else "insufficient"
    return {
        "selected_context": selected_context,
        "retrieval_quality": quality,
    }
