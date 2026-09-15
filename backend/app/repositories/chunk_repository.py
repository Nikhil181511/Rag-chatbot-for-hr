import uuid
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy import select, delete, func, text, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.chunk import DocumentChunk
from app.models.document import DocumentVersion, Document, DocumentStatus


class ChunkRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def bulk_insert_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        self.session.add_all(chunks)
        await self.session.flush()
        return chunks

    async def delete_by_document_version_id(self, document_version_id: uuid.UUID) -> int:
        stmt = delete(DocumentChunk).where(
            DocumentChunk.document_version_id == document_version_id
        )
        result = await self.session.execute(stmt)
        return result.rowcount or 0

    async def get_by_ids(self, chunk_ids: List[uuid.UUID]) -> List[DocumentChunk]:
        if not chunk_ids:
            return []
        stmt = (
            select(DocumentChunk)
            .options(joinedload(DocumentChunk.document_version).joinedload(DocumentVersion.document))
            .where(DocumentChunk.id.in_(chunk_ids))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def dense_search(
        self,
        query_embedding: List[float],
        top_k: int = 30,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Cosine distance search via pgvector: 1 - (embedding <=> query_embedding) = cosine similarity.
        Only queries chunks from current versions of READY documents.
        """
        distance_expr = DocumentChunk.embedding.cosine_distance(query_embedding).label("distance")

        stmt = (
            select(DocumentChunk, distance_expr)
            .options(joinedload(DocumentChunk.document_version).joinedload(DocumentVersion.document))
            .join(DocumentVersion, DocumentChunk.document_version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .where(
                and_(
                    DocumentVersion.is_current.is_(True),
                    Document.status == DocumentStatus.READY,
                )
            )
        )

        if filters:
            if "document_category" in filters and filters["document_category"]:
                stmt = stmt.where(Document.document_category == filters["document_category"])
            if "document_id" in filters and filters["document_id"]:
                stmt = stmt.where(Document.id == uuid.UUID(str(filters["document_id"])))

        stmt = stmt.order_by(distance_expr.asc()).limit(top_k)
        result = await self.session.execute(stmt)

        # Convert distance to similarity score: similarity = 1 - distance
        return [(row[0], float(1.0 - row[1])) for row in result.all()]

    async def sparse_search(
        self,
        query_text: str,
        top_k: int = 30,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Tuple[DocumentChunk, float]]:
        """
        Full-text search using tsvector and ts_rank_cd on english dictionary.
        """
        tsquery = func.plainto_tsquery("english", query_text)
        rank_expr = func.ts_rank_cd(DocumentChunk.tsvector_content, tsquery).label("rank")

        stmt = (
            select(DocumentChunk, rank_expr)
            .options(joinedload(DocumentChunk.document_version).joinedload(DocumentVersion.document))
            .join(DocumentVersion, DocumentChunk.document_version_id == DocumentVersion.id)
            .join(Document, DocumentVersion.document_id == Document.id)
            .where(
                and_(
                    DocumentVersion.is_current.is_(True),
                    Document.status == DocumentStatus.READY,
                    DocumentChunk.tsvector_content.op("@@")(tsquery),
                )
            )
        )

        if filters:
            if "document_category" in filters and filters["document_category"]:
                stmt = stmt.where(Document.document_category == filters["document_category"])
            if "document_id" in filters and filters["document_id"]:
                stmt = stmt.where(Document.id == uuid.UUID(str(filters["document_id"])))

        stmt = stmt.order_by(rank_expr.desc()).limit(top_k)
        result = await self.session.execute(stmt)
        return [(row[0], float(row[1])) for row in result.all()]
