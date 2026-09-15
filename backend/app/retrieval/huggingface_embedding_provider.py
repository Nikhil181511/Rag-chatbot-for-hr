from typing import List
from app.retrieval.embedding_provider import EmbeddingProvider
from app.config.logging import get_logger

logger = get_logger(__name__)


class HuggingFaceEmbeddingProvider(EmbeddingProvider):
    _model = None

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", dimension: int = 1536):
        self._model_name = model_name
        self._dimension = dimension

    def _get_model(self):
        if HuggingFaceEmbeddingProvider._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info("Loading HuggingFace local embedding model", model=self._model_name)
                HuggingFaceEmbeddingProvider._model = SentenceTransformer(self._model_name)
            except Exception as e:
                logger.warning("Could not load SentenceTransformer", error=str(e))
                HuggingFaceEmbeddingProvider._model = False
        return HuggingFaceEmbeddingProvider._model

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._get_model()
        if not model:
            # Deterministic fallback
            from app.retrieval.openai_embedding_provider import OpenAIEmbeddingProvider
            mock = OpenAIEmbeddingProvider()
            return [mock._mock_embedding(t) for t in texts]

        embeddings = model.encode(texts, convert_to_numpy=True)
        results = []
        for emb in embeddings:
            raw = [float(x) for x in emb]
            # Pad to 1536 dimensions
            if len(raw) < self._dimension:
                raw = raw + [0.0] * (self._dimension - len(raw))
            elif len(raw) > self._dimension:
                raw = raw[: self._dimension]
            results.append(raw)
        return results

    async def embed_query(self, query: str) -> List[float]:
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * self._dimension
