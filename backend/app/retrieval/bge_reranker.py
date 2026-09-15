import asyncio
from typing import List
from app.retrieval.reranker import Reranker, ChunkCandidate
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class BGEReranker(Reranker):
    _model = None

    def __init__(self, model_name: str = settings.BGE_MODEL_NAME):
        self.model_name = model_name

    def _get_model(self):
        if BGEReranker._model is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info("Loading BGE Reranker model", model=self.model_name)
                BGEReranker._model = CrossEncoder(self.model_name, max_length=512)
                logger.info("BGE Reranker model loaded successfully")
            except Exception as e:
                logger.warning("Could not load CrossEncoder model, fallback to score sorting", error=str(e))
                BGEReranker._model = False
        return BGEReranker._model

    async def rerank(
        self, query: str, candidates: List[ChunkCandidate], top_k: int = 10
    ) -> List[ChunkCandidate]:
        if not candidates:
            return []

        model = self._get_model()
        if not model:
            # Fallback to current score ranking
            sorted_candidates = sorted(candidates, key=lambda c: c.score, reverse=True)
            return sorted_candidates[:top_k]

        pairs = [[query, c.content] for c in candidates]

        # Run CPU/GPU bound scoring in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        scores = await loop.run_in_executor(None, lambda: model.predict(pairs))

        scored_candidates = []
        for candidate, score in zip(candidates, scores):
            scored_candidates.append(
                ChunkCandidate(
                    chunk_id=candidate.chunk_id,
                    document_id=candidate.document_id,
                    document_name=candidate.document_name,
                    content=candidate.content,
                    score=float(score),
                    page_number=candidate.page_number,
                    section=candidate.section,
                    sheet_name=candidate.sheet_name,
                    row_start=candidate.row_start,
                    row_end=candidate.row_end,
                    source="bge_reranked",
                    metadata=candidate.metadata,
                )
            )

        scored_candidates.sort(key=lambda c: c.score, reverse=True)
        return scored_candidates[:top_k]
