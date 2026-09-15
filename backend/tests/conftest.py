import pytest
import asyncio
from typing import AsyncGenerator
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.config.settings import Settings, settings
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_settings() -> Settings:
    return Settings(
        APP_ENV="testing",
        LOG_LEVEL="DEBUG",
        POSTGRES_DB="hr_rag_test_db",
        LLM_PROVIDER="openai",
        RERANKER_PROVIDER="none",
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    app = create_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
