import uuid
from typing import List, Dict
from app.retrieval.reranker import ChunkCandidate


def reciprocal_rank_fusion(
    dense_candidates: List[ChunkCandidate],
    sparse_candidates: List[ChunkCandidate],
    k: int = 60,
    top_k: int = 50,
) -> List[ChunkCandidate]:
    """
    Computes reciprocal rank fusion (RRF) scores across dense and sparse ranking lists.
    Formula: RRF_score(d) = sum(1 / (k + rank(d)))
    """
    scores: Dict[uuid.UUID, float] = {}
    candidate_map: Dict[uuid.UUID, ChunkCandidate] = {}

    # Dense rankings (1-indexed rank)
    for rank, candidate in enumerate(dense_candidates, start=1):
        c_id = candidate.chunk_id
        scores[c_id] = scores.get(c_id, 0.0) + (1.0 / (k + rank))
        if c_id not in candidate_map:
            candidate_map[c_id] = candidate

    # Sparse rankings (1-indexed rank)
    for rank, candidate in enumerate(sparse_candidates, start=1):
        c_id = candidate.chunk_id
        scores[c_id] = scores.get(c_id, 0.0) + (1.0 / (k + rank))
        if c_id not in candidate_map:
            candidate_map[c_id] = candidate

    # Create fused candidates with RRF scores
    fused_candidates: List[ChunkCandidate] = []
    for c_id, score in scores.items():
        base = candidate_map[c_id]
        fused = ChunkCandidate(
            chunk_id=base.chunk_id,
            document_id=base.document_id,
            document_name=base.document_name,
            content=base.content,
            score=score,
            page_number=base.page_number,
            section=base.section,
            sheet_name=base.sheet_name,
            row_start=base.row_start,
            row_end=base.row_end,
            source="rrf_fused",
            metadata=base.metadata,
        )
        fused_candidates.append(fused)

    # Sort descending by fused score
    fused_candidates.sort(key=lambda c: c.score, reverse=True)
    return fused_candidates[:top_k]
