from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.knowledge_base_service import KnowledgeBaseService
from app.schemas.document import KnowledgeBaseStats

router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


@router.get("/stats", response_model=KnowledgeBaseStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    return await service.get_stats()


@router.get("/health")
async def get_health(db: AsyncSession = Depends(get_db)):
    service = KnowledgeBaseService(db)
    stats = await service.get_stats()
    return {
        "status": "healthy" if stats.failed_count == 0 else "degraded",
        "stats": stats,
    }
