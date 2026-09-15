import asyncio
import uuid
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.chunk_repository import ChunkRepository
from app.retrieval.embedding_factory import EmbeddingFactory
from app.retrieval.reranker import ChunkCandidate
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


class HybridRetriever:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.chunk_repo = ChunkRepository(session)
        self.embedding_provider = EmbeddingFactory.get_provider()

    async def retrieve(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        dense_top_k: int = settings.DENSE_TOP_K,
        sparse_top_k: int = settings.SPARSE_TOP_K,
    ) -> Dict[str, List[ChunkCandidate]]:
        """
        Executes dense vector search and sparse full-text search concurrently.
        Returns dictionary with 'dense' and 'sparse' candidate lists.
        """
        # 1. Generate query embedding
        query_embedding = await self.embedding_provider.embed_query(query)

        # 2. Execute dense and sparse searches sequentially to avoid concurrent session usage
        dense_results = await self.chunk_repo.dense_search(
            query_embedding=query_embedding,
            top_k=dense_top_k,
            filters=filters,
        )
        sparse_results = await self.chunk_repo.sparse_search(
            query_text=query,
            top_k=sparse_top_k,
            filters=filters,
        )

        # 3. Convert to ChunkCandidate objects
        dense_candidates: List[ChunkCandidate] = []
        for chunk, score in dense_results:
            doc_name = (
                chunk.document_version.document.file_name
                if chunk.document_version and chunk.document_version.document
                else "Document"
            )
            doc_id = (
                chunk.document_version.document.id
                if chunk.document_version and chunk.document_version.document
                else chunk.document_version_id
            )
            dense_candidates.append(
                ChunkCandidate(
                    chunk_id=chunk.id,
                    document_id=doc_id,
                    document_name=doc_name,
                    content=chunk.content,
                    score=score,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    sheet_name=chunk.sheet_name,
                    row_start=chunk.row_start,
                    row_end=chunk.row_end,
                    source="dense",
                    metadata=chunk.chunk_metadata,
                )
            )

        sparse_candidates: List[ChunkCandidate] = []
        for chunk, score in sparse_results:
            doc_name = (
                chunk.document_version.document.file_name
                if chunk.document_version and chunk.document_version.document
                else "Document"
            )
            doc_id = (
                chunk.document_version.document.id
                if chunk.document_version and chunk.document_version.document
                else chunk.document_version_id
            )
            sparse_candidates.append(
                ChunkCandidate(
                    chunk_id=chunk.id,
                    document_id=doc_id,
                    document_name=doc_name,
                    content=chunk.content,
                    score=score,
                    page_number=chunk.page_number,
                    section=chunk.section,
                    sheet_name=chunk.sheet_name,
                    row_start=chunk.row_start,
                    row_end=chunk.row_end,
                    source="sparse",
                    metadata=chunk.chunk_metadata,
                )
            )

        logger.info(
            "Hybrid retrieval completed",
            dense_count=len(dense_candidates),
            sparse_count=len(sparse_candidates),
        )

        return {
            "dense": dense_candidates,
            "sparse": sparse_candidates,
        }
