import uuid
from typing import Optional, List, Sequence
from datetime import datetime
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.document import Document, DocumentVersion, DocumentStatus


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.chunks))
            .where(Document.id == document_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> Optional[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.chunks))
            .where(Document.content_hash == content_hash)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_documents(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[DocumentStatus] = None,
    ) -> Sequence[Document]:
        stmt = (
            select(Document)
            .options(selectinload(Document.versions).selectinload(DocumentVersion.chunks))
            .order_by(Document.created_at.desc())
        )
        if status:
            stmt = stmt.where(Document.status == status)
        stmt = stmt.offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_document(
        self,
        file_name: str,
        file_type: str,
        file_size: int,
        content_hash: str,
        storage_path: str,
        title: Optional[str] = None,
        document_category: Optional[str] = None,
        status: DocumentStatus = DocumentStatus.PENDING,
    ) -> Document:
        doc = Document(
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            content_hash=content_hash,
            storage_path=storage_path,
            title=title or file_name,
            document_category=document_category,
            status=status,
        )
        self.session.add(doc)
        await self.session.flush()
        return doc

    async def update_status(
        self,
        document_id: uuid.UUID,
        status: DocumentStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Document]:
        doc = await self.get_by_id(document_id)
        if not doc:
            return None
        doc.status = status
        doc.error_message = error_message
        doc.updated_at = datetime.utcnow()
        await self.session.flush()
        return doc

    async def create_version(
        self,
        document_id: uuid.UUID,
        version_number: int,
        content_hash: str,
        embedding_model: str,
        embedding_dim: int = 1536,
        parser_version: str = "1.0.0",
        index_version: str = "v1",
        effective_date: Optional[datetime] = None,
        expiry_date: Optional[datetime] = None,
        is_current: bool = True,
    ) -> DocumentVersion:
        if is_current:
            # Set other versions to is_current=False
            await self.session.execute(
                update(DocumentVersion)
                .where(DocumentVersion.document_id == document_id)
                .values(is_current=False)
            )
        
        doc_version = DocumentVersion(
            document_id=document_id,
            version=version_number,
            content_hash=content_hash,
            parser_version=parser_version,
            embedding_model=embedding_model,
            embedding_dim=embedding_dim,
            index_version=index_version,
            effective_date=effective_date,
            expiry_date=expiry_date,
            is_current=is_current,
        )
        self.session.add(doc_version)
        await self.session.flush()
        return doc_version

    async def get_current_version(self, document_id: uuid.UUID) -> Optional[DocumentVersion]:
        stmt = select(DocumentVersion).where(
            DocumentVersion.document_id == document_id,
            DocumentVersion.is_current.is_(True),
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        stmt = delete(Document).where(Document.id == document_id)
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0
