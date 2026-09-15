import math
import hashlib
from typing import List
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from app.retrieval.embedding_provider import EmbeddingProvider
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(
        self,
        api_key: str = "",
        model: str = "gemini-embedding-001",
        dimension: int = 1536,
    ):
        self._model = model
        self._dimension = dimension
        self._api_key = api_key or settings.effective_llm_key
        if self._api_key:
            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url=settings.GEMINI_BASE_URL,
            )
        else:
            self._client = None

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _mock_embedding(self, text: str) -> List[float]:
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
            logger.warning("No Gemini API key provided, using deterministic embeddings")
            return [self._mock_embedding(t) for t in texts]

        try:
            # Batch call via Gemini OpenAI-compatible endpoint
            response = await self._client.embeddings.create(
                input=texts,
                model=self._model,
            )
            raw_embeddings = [d.embedding for d in sorted(response.data, key=lambda x: x.index)]
            
            # Slice/pad and normalize to match PostgreSQL schema dimension (1536)
            padded = []
            for emb in raw_embeddings:
                if len(emb) < self._dimension:
                    emb = emb + [0.0] * (self._dimension - len(emb))
                elif len(emb) > self._dimension:
                    emb = emb[: self._dimension]
                norm = math.sqrt(sum(x * x for x in emb)) or 1.0
                padded.append([x / norm for x in emb])
            return padded
        except Exception as e:
            logger.warning("Gemini embedding API failed, falling back to local embeddings", error=str(e))
            return [self._mock_embedding(t) for t in texts]

    async def embed_query(self, query: str) -> List[float]:
        results = await self.embed_texts([query])
        return results[0] if results else [0.0] * self._dimension
