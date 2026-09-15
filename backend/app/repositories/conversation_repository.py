import uuid
from typing import Optional, List, Sequence, Dict, Any
from datetime import datetime
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, conversation_id: uuid.UUID) -> Optional[Conversation]:
        stmt = (
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_conversations(
        self, skip: int = 0, limit: int = 50
    ) -> Sequence[Conversation]:
        stmt = select(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_conversation(
        self,
        conversation_id: Optional[uuid.UUID] = None,
        title: str = "New Conversation",
    ) -> Conversation:
        conv = Conversation(
            id=conversation_id or uuid.uuid4(),
            title=title,
            message_count=0,
        )
        self.session.add(conv)
        await self.session.flush()
        return conv

    async def get_or_create(
        self,
        conversation_id: Optional[uuid.UUID] = None,
        title: Optional[str] = None,
    ) -> Conversation:
        if conversation_id:
            conv = await self.get_by_id(conversation_id)
            if conv:
                return conv
        return await self.create_conversation(
            conversation_id=conversation_id,
            title=title or "New Conversation",
        )

    async def get_messages_window(
        self, conversation_id: uuid.UUID, limit: int = 20
    ) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        messages = list(result.scalars().all())
        # Return chronological order
        return sorted(messages, key=lambda m: m.created_at)

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        rag_run_id: Optional[uuid.UUID] = None,
        citations: Optional[List[Dict[str, Any]]] = None,
    ) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            rag_run_id=rag_run_id,
            citations=citations,
        )
        self.session.add(msg)

        # Update conversation message_count and updated_at
        await self.session.execute(
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(
                message_count=Conversation.message_count + 1,
                updated_at=datetime.utcnow(),
            )
        )
        await self.session.flush()
        return msg

    async def update_title(self, conversation_id: uuid.UUID, title: str) -> Optional[Conversation]:
        conv = await self.get_by_id(conversation_id)
        if conv:
            conv.title = title
            conv.updated_at = datetime.utcnow()
            await self.session.flush()
        return conv

    async def delete_conversation(self, conversation_id: uuid.UUID) -> bool:
        stmt = delete(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0
