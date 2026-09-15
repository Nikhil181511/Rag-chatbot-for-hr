import math
import hashlib
from typing import List
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.retrieval.embedding_provider import EmbeddingProvider
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str = settings.LLM_API_KEY,
        model: str = settings.EMBEDDING_MODEL,
        dimension: int = settings.EMBEDDING_DIMENSION,
    ):
        self._model = model
        self._dimension = dimension
        self._api_key = api_key
        self._client = AsyncOpenAI(api_key=api_key) if api_key else None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _mock_embedding(self, text: str) -> List[float]:
        """Deterministic pseudo-embedding for testing when no OpenAI API key is present."""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = [float((b / 255.0) * 2 - 1) for b in h]
        while len(vec) < self._dimension:
            vec.extend(vec[: min(len(vec), self._dimension - len(vec))])
        vec = vec[: self._dimension]
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True,
    )
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        if not self._client or not self._api_key:
            logger.warning("No OpenAI API key provided, using deterministic mock embeddings")
            return [self._mock_embedding(t) for t in texts]

        # OpenAI batch embedding (chunk into batches of 100)
        batch_size = 100
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self._client.embeddings.create(
                input=batch,
                model=self._model,
            )
            # Sort embeddings by index to preserve order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

        return all_embeddings

    async def embed_query(self, query: str) -> List[float]:
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * self._dimension
