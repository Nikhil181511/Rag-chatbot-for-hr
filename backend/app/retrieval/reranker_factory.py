from typing import Optional
from app.retrieval.reranker import Reranker, NoOpReranker
from app.retrieval.bge_reranker import BGEReranker
from app.retrieval.cohere_reranker import CohereReranker
from app.config.settings import settings


class RerankerFactory:
    _instance: Optional[Reranker] = None

    @classmethod
    def get_reranker(cls, override_provider: Optional[str] = None) -> Reranker:
        provider = (override_provider or settings.RERANKER_PROVIDER).lower()

        if provider == "none":
            return NoOpReranker()
        elif provider == "cohere":
            return CohereReranker(api_key=settings.COHERE_API_KEY)
        elif provider == "bge":
            if cls._instance is None or not isinstance(cls._instance, BGEReranker):
                cls._instance = BGEReranker(model_name=settings.BGE_MODEL_NAME)
            return cls._instance
        return NoOpReranker()
