import asyncio
from app.config.database import engine
from app.models.base import Base
import app.models.document
import app.models.chunk
import app.models.conversation
import app.models.rag_run
import app.models.evaluation


async def init_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables initialized successfully.")


if __name__ == "__main__":
    asyncio.run(init_tables())
