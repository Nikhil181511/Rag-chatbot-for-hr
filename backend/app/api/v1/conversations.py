import uuid
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ConversationItem,
    ConversationListResponse,
    ConversationDetailResponse,
    ConversationCreateResponse,
    MessageItem,
)

router = APIRouter(prefix="/conversations", tags=["Conversations"])


@router.post("", response_model=ConversationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(db: AsyncSession = Depends(get_db)):
    repo = ConversationRepository(db)
    conv = await repo.create_conversation()
    return ConversationCreateResponse(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
    )


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    convs = await repo.list_conversations(skip=skip, limit=limit)
    items = [
        ConversationItem(
            id=c.id,
            title=c.title,
            message_count=c.message_count,
            updated_at=c.updated_at,
        )
        for c in convs
    ]
    return ConversationListResponse(conversations=items)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    messages = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            rag_run_id=m.rag_run_id,
            citations=m.citations,
            created_at=m.created_at,
        )
        for m in conv.messages
    ]
    return ConversationDetailResponse(
        id=conv.id,
        title=conv.title,
        messages=messages,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    repo = ConversationRepository(db)
    deleted = await repo.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation {conversation_id} not found",
        )
    return None
