from typing import Optional
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)

_langfuse_client = None


def get_langfuse():
    global _langfuse_client
    if _langfuse_client is not None:
        return _langfuse_client

    if not settings.LANGFUSE_PUBLIC_KEY or not settings.LANGFUSE_SECRET_KEY:
        return None

    try:
        from langfuse import Langfuse

        _langfuse_client = Langfuse(
            public_key=settings.LANGFUSE_PUBLIC_KEY,
            secret_key=settings.LANGFUSE_SECRET_KEY,
            host=settings.LANGFUSE_BASE_URL,
        )
        logger.info("Langfuse client initialized successfully", host=settings.LANGFUSE_BASE_URL)
        return _langfuse_client
    except Exception as e:
        logger.warning("Failed to initialize Langfuse client", error=str(e))
        return None
