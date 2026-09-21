from fastapi import APIRouter, Depends, status, Response, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.chat_service import ChatService
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import require_employee_or_hr
from app.models.user import User

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employee_or_hr),
):
    service = ChatService(db)
    return await service.execute_chat(request)


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employee_or_hr),
):
    service = ChatService(db)
    return StreamingResponse(
        service.stream_chat(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/stream/{request_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_stream(request_id: str):
    cancelled = ChatService.cancel_stream(request_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Streaming request {request_id} not found or already completed.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
