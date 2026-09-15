import uuid
from typing import List, Set


class RetrievalMetrics:
    @staticmethod
    def precision_at_k(retrieved_ids: List[uuid.UUID], relevant_ids: Set[uuid.UUID], k: int = 5) -> float:
        if not retrieved_ids or k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for cid in top_k if cid in relevant_ids)
        return hits / len(top_k)

    @staticmethod
    def recall_at_k(retrieved_ids: List[uuid.UUID], relevant_ids: Set[uuid.UUID], k: int = 5) -> float:
        if not relevant_ids or k <= 0:
            return 0.0
        top_k = retrieved_ids[:k]
        hits = sum(1 for cid in top_k if cid in relevant_ids)
        return hits / len(relevant_ids)

    @staticmethod
    def mean_reciprocal_rank(retrieved_ids: List[uuid.UUID], relevant_ids: Set[uuid.UUID]) -> float:
        for rank, cid in enumerate(retrieved_ids, start=1):
            if cid in relevant_ids:
                return 1.0 / rank
        return 0.0

    @staticmethod
    def hit_rate(retrieved_ids: List[uuid.UUID], relevant_ids: Set[uuid.UUID], k: int = 5) -> float:
        top_k = retrieved_ids[:k]
        return 1.0 if any(cid in relevant_ids for cid in top_k) else 0.0
