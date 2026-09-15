from abc import ABC, abstractmethod
from typing import List


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def dimension(self) -> int:
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of document chunk texts."""
        pass

    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Generate a vector embedding for a single search query."""
        pass
