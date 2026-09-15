from typing import List, Dict, Any
from app.retrieval.reranker import ChunkCandidate
from app.ingestion.chunking.base import count_tokens
from app.config.settings import settings


class ContextSelector:
    def __init__(
        self,
        max_chunks: int = settings.FINAL_CONTEXT_CHUNKS,
        max_token_budget: int = 3000,
    ):
        self.max_chunks = max_chunks
        self.max_token_budget = max_token_budget

    def select(
        self, candidates: List[ChunkCandidate]
    ) -> List[Dict[str, Any]]:
        selected: List[Dict[str, Any]] = []
        current_tokens = 0
        seen_ids = set()

        for candidate in candidates:
            if candidate.chunk_id in seen_ids:
                continue
            if len(selected) >= self.max_chunks:
                break

            chunk_tokens = count_tokens(candidate.content)
            if current_tokens + chunk_tokens > self.max_token_budget and selected:
                # Token budget exceeded and we already have at least 1 chunk
                break

            seen_ids.add(candidate.chunk_id)
            current_tokens += chunk_tokens

            # Create excerpt (first 200 chars or summary)
            excerpt = candidate.content[:250].strip().replace("\n", " ") + "..."

            selected.append({
                "chunk_id": str(candidate.chunk_id),
                "document_id": str(candidate.document_id),
                "document_name": candidate.document_name,
                "content": candidate.content,
                "score": candidate.score,
                "page_number": candidate.page_number,
                "section": candidate.section,
                "sheet_name": candidate.sheet_name,
                "row_start": candidate.row_start,
                "row_end": candidate.row_end,
                "excerpt": excerpt,
                "token_count": chunk_tokens,
            })

        return selected
