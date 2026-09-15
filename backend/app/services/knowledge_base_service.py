from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus, DocumentVersion
from app.models.chunk import DocumentChunk
from app.schemas.document import KnowledgeBaseStats


class KnowledgeBaseService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_stats(self) -> KnowledgeBaseStats:
        # Total documents count
        total_stmt = select(func.count(Document.id)).where(Document.status != DocumentStatus.DELETED)
        total_res = await self.session.execute(total_stmt)
        total_docs = total_res.scalar() or 0

        # Ready documents
        ready_stmt = select(func.count(Document.id)).where(Document.status == DocumentStatus.READY)
        ready_res = await self.session.execute(ready_stmt)
        ready_docs = ready_res.scalar() or 0

        # Failed documents
        failed_stmt = select(func.count(Document.id)).where(Document.status == DocumentStatus.FAILED)
        failed_res = await self.session.execute(failed_stmt)
        failed_docs = failed_res.scalar() or 0

        # Total chunks count
        chunks_stmt = select(func.count(DocumentChunk.id))
        chunks_res = await self.session.execute(chunks_stmt)
        total_chunks = chunks_res.scalar() or 0

        # Last indexed at
        last_indexed_stmt = (
            select(DocumentVersion.created_at)
            .order_by(DocumentVersion.created_at.desc())
            .limit(1)
        )
        last_indexed_res = await self.session.execute(last_indexed_stmt)
        last_indexed_at = last_indexed_res.scalar_one_or_none()

        return KnowledgeBaseStats(
            document_count=total_docs,
            ready_count=ready_docs,
            failed_count=failed_docs,
            total_chunks=total_chunks,
            last_indexed_at=last_indexed_at,
        )
