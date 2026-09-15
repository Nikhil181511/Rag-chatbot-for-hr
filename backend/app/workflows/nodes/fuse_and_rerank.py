import uuid
from typing import Dict, Any, List
from app.workflows.graph_state import RAGState
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.reranker_factory import RerankerFactory
from app.retrieval.reranker import ChunkCandidate


async def fuse_and_rerank_node(state: RAGState) -> Dict[str, Any]:
    dense = state.get("_raw_dense") or []
    sparse = state.get("_raw_sparse") or []
    query = state.get("original_query", "")

    # Reconstruct from retrieved_candidates if raw lists are empty
    if not dense and not sparse:
        candidates = state.get("retrieved_candidates", [])
        for c in candidates:
            cand = ChunkCandidate(
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
                source=c.get("source", "dense"),
                metadata=c.get("metadata", {}),
            )
            if c.get("source") == "sparse":
                sparse.append(cand)
            else:
                dense.append(cand)

    # 1. RRF Fusion
    fused_candidates: List[ChunkCandidate] = reciprocal_rank_fusion(
        dense_candidates=dense,
        sparse_candidates=sparse,
    )

    # 2. Reranking
    reranker = RerankerFactory.get_reranker()
    reranked_candidates = await reranker.rerank(
        query=query,
        candidates=fused_candidates,
        top_k=10,
    )

    return {
        "fused_candidates": [
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
            for c in fused_candidates
        ],
        "reranked_candidates": [
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
            for c in reranked_candidates
        ],
        "_raw_reranked": reranked_candidates,
    }
