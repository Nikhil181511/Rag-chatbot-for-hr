from datetime import datetime
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.common import HealthResponse, ReadyResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def get_health():
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get("/ready", response_model=ReadyResponse)
async def get_ready(db: AsyncSession = Depends(get_db)):
    db_status = "error"
    vector_status = "error"
    error_msg = None

    try:
        # Check database connectivity
        res = await db.execute(text("SELECT 1"))
        if res.scalar() == 1:
            db_status = "ok"

        # Check pgvector extension availability
        vec_res = await db.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        )
        if vec_res.scalar_one_or_none() == "vector":
            vector_status = "ok"
        else:
            error_msg = "Vector extension not found"
    except Exception as e:
        error_msg = str(e)

    if db_status == "ok" and vector_status == "ok":
        return ReadyResponse(
            status="ready",
            database="ok",
            vector_index="ok",
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "database": db_status,
                "vector_index": vector_status,
                "message": error_msg or "Service components not ready",
            },
        )
