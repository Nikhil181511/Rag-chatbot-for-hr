import os
import uuid
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.chunk import DocumentChunk
from app.repositories.document_repository import DocumentRepository
from app.repositories.chunk_repository import ChunkRepository
from app.ingestion.loaders.loader_factory import LoaderFactory, UnsupportedFileTypeError
from app.ingestion.chunking.chunker_factory import ChunkerFactory
from app.ingestion.metadata import MetadataEnricher
from app.retrieval.embedding_factory import EmbeddingFactory
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".xlsx", ".csv"}


class InvalidFileError(Exception):
    pass


class IngestionPipeline:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.chunk_repo = ChunkRepository(session)
        self.embedding_provider = EmbeddingFactory.get_provider()

    @classmethod
    def validate_file(cls, file_name: str, file_size: int) -> None:
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise InvalidFileError(
                f"File type '{ext}' is not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_size_bytes:
            raise InvalidFileError(
                f"File size {file_size / (1024*1024):.2f}MB exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
            )

    async def run(self, document_id: uuid.UUID) -> Document:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise ValueError(f"Document {document_id} not found")

        try:
            # 1. Update status to PROCESSING
            await self.doc_repo.update_status(document_id, DocumentStatus.PROCESSING)
            logger.info("Starting document ingestion", document_id=str(document_id), file_name=doc.file_name)

            # 2. Load and normalize document
            loader = LoaderFactory.get_loader(doc.file_name)
            normalized_doc = loader.load(doc.storage_path, original_filename=doc.file_name)

            # 3. Enrich document metadata
            hr_metadata = MetadataEnricher.enrich_document(
                title=normalized_doc.title,
                content=normalized_doc.content,
            )
            doc.title = normalized_doc.title
            if hr_metadata.get("document_category"):
                doc.document_category = hr_metadata["document_category"]

            # 4. Chunk document
            chunker = ChunkerFactory.get_chunker(normalized_doc.source_type)
            raw_chunks = chunker.chunk(normalized_doc)

            if not raw_chunks:
                raise ValueError("Document produced 0 chunks after parsing")

            # 5. Update status to INDEXING
            await self.doc_repo.update_status(document_id, DocumentStatus.INDEXING)

            # 6. Create Document Version
            existing_versions = doc.versions or []
            new_version_num = len(existing_versions) + 1

            doc_version = await self.doc_repo.create_version(
                document_id=document_id,
                version_number=new_version_num,
                content_hash=doc.content_hash,
                embedding_model=self.embedding_provider.model_name,
                embedding_dim=self.embedding_provider.dimension,
                is_current=True,
            )

            # 7. Generate vector embeddings in batch
            chunk_texts = [c.content for c in raw_chunks]
            embeddings = await self.embedding_provider.embed_texts(chunk_texts)

            # 8. Prepare DocumentChunk ORM models
            db_chunks: List[DocumentChunk] = []
            for raw_chunk, emb in zip(raw_chunks, embeddings):
                db_chunk = DocumentChunk(
                    document_version_id=doc_version.id,
                    chunk_index=raw_chunk.chunk_index,
                    content=raw_chunk.content,
                    content_hash=raw_chunk.content_hash,
                    token_count=raw_chunk.token_count,
                    page_number=raw_chunk.page_number,
                    section=raw_chunk.section,
                    parent_section=raw_chunk.parent_section,
                    sheet_name=raw_chunk.sheet_name,
                    row_start=raw_chunk.row_start,
                    row_end=raw_chunk.row_end,
                    is_ocr=raw_chunk.is_ocr,
                    chunk_metadata=raw_chunk.metadata,
                    embedding=emb,
                )
                db_chunks.append(db_chunk)

            # 9. Bulk insert chunks
            await self.chunk_repo.bulk_insert_chunks(db_chunks)

            # 10. Update status to READY
            updated_doc = await self.doc_repo.update_status(document_id, DocumentStatus.READY)
            logger.info(
                "Document ingestion completed successfully",
                document_id=str(document_id),
                chunks_count=len(db_chunks),
            )
            return updated_doc or doc

        except Exception as e:
            logger.error(
                "Document ingestion failed",
                document_id=str(document_id),
                exc_info=e,
            )
            await self.doc_repo.update_status(
                document_id, DocumentStatus.FAILED, error_message=str(e)
            )
            raise
