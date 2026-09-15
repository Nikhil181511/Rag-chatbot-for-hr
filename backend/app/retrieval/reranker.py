import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ChunkCandidate:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    document_name: str
    content: str
    score: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    sheet_name: Optional[str] = None
    row_start: Optional[int] = None
    row_end: Optional[int] = None
    source: str = "dense"  # "dense" | "sparse" | "fused" | "reranked"
    metadata: Dict[str, Any] = field(default_factory=dict)


class Reranker(ABC):
    @abstractmethod
    async def rerank(
        self, query: str, candidates: List[ChunkCandidate], top_k: int = 10
    ) -> List[ChunkCandidate]:
        """Rerank candidates based on semantic relevance to the query."""
        pass


class NoOpReranker(Reranker):
    async def rerank(
        self, query: str, candidates: List[ChunkCandidate], top_k: int = 10
    ) -> List[ChunkCandidate]:
        sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
        return sorted_candidates[:top_k]
