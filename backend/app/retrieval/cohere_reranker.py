from typing import List
from app.retrieval.reranker import Reranker, ChunkCandidate
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class CohereReranker(Reranker):
    def __init__(self, api_key: str = settings.COHERE_API_KEY):
        self.api_key = api_key
        self._client = None
        if api_key:
            try:
                import cohere
                self._client = cohere.AsyncClientV2(api_key=api_key)
            except Exception as e:
                logger.warning("Could not initialize Cohere client", error=str(e))

    async def rerank(
        self, query: str, candidates: List[ChunkCandidate], top_k: int = 10
    ) -> List[ChunkCandidate]:
        if not candidates:
            return []

        if not self._client:
            logger.warning("Cohere client not initialized, falling back to rank order")
            sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
            return sorted_candidates[:top_k]

        try:
            docs = [c.content for c in candidates]
            response = await self._client.rerank(
                model="rerank-v3.5",
                query=query,
                documents=docs,
                top_n=min(top_k, len(candidates)),
            )

            reranked: List[ChunkCandidate] = []
            for item in response.results:
                orig_candidate = candidates[item.index]
                reranked.append(
                    ChunkCandidate(
                        chunk_id=orig_candidate.chunk_id,
                        document_id=orig_candidate.document_id,
                        document_name=orig_candidate.document_name,
                        content=orig_candidate.content,
                        score=float(item.relevance_score),
                        page_number=orig_candidate.page_number,
                        section=orig_candidate.section,
                        sheet_name=orig_candidate.sheet_name,
                        row_start=orig_candidate.row_start,
                        row_end=orig_candidate.row_end,
                        source="cohere_reranked",
                        metadata=orig_candidate.metadata,
                    )
                )
            return reranked

        except Exception as e:
            logger.error("Cohere rerank failed, falling back to input ranking", exc_info=e)
            sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
            return sorted_candidates[:top_k]
