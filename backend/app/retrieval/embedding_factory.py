from typing import Optional
from app.retrieval.embedding_provider import EmbeddingProvider
from app.retrieval.openai_embedding_provider import OpenAIEmbeddingProvider
from app.retrieval.gemini_embedding_provider import GeminiEmbeddingProvider
from app.retrieval.huggingface_embedding_provider import HuggingFaceEmbeddingProvider
from app.config.settings import settings


class EmbeddingFactory:
    _instance: Optional[EmbeddingProvider] = None

    @classmethod
    def get_provider(cls) -> EmbeddingProvider:
        if cls._instance is None:
            provider_type = settings.EMBEDDING_PROVIDER.lower()
            if provider_type == "gemini":
                cls._instance = GeminiEmbeddingProvider(
                    api_key=settings.effective_llm_key,
                    model="gemini-embedding-002",
                    dimension=settings.EMBEDDING_DIMENSION,
                )
            elif provider_type == "huggingface":
                cls._instance = HuggingFaceEmbeddingProvider(
                    dimension=settings.EMBEDDING_DIMENSION,
                )
            elif provider_type == "openai":
                if settings.LLM_PROVIDER == "gemini" and not settings.LLM_API_KEY.startswith("sk-"):
                    # Automatically use Gemini embeddings when Gemini is configured
                    cls._instance = GeminiEmbeddingProvider(
                        api_key=settings.effective_llm_key,
                        model="gemini-embedding-002",
                        dimension=settings.EMBEDDING_DIMENSION,
                    )
                else:
                    cls._instance = OpenAIEmbeddingProvider(
                        api_key=settings.LLM_API_KEY,
                        model=settings.EMBEDDING_MODEL,
                        dimension=settings.EMBEDDING_DIMENSION,
                    )
            else:
                cls._instance = HuggingFaceEmbeddingProvider(
                    dimension=settings.EMBEDDING_DIMENSION,
                )
        return cls._instance
