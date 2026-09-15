import os
import uuid
import hashlib
import asyncio
from typing import List, Optional, Sequence
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.ingestion.pipeline import IngestionPipeline, InvalidFileError
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger(__name__)


def _write_file_sync(file_path: str, content: bytes) -> None:
    with open(file_path, "wb") as f:
        f.write(content)


class DocumentService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.doc_repo = DocumentRepository(session)
        self.pipeline = IngestionPipeline(session)

    async def upload_document(self, file: UploadFile) -> Document:
        file_name = file.filename or "unknown"
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # 1. Read file content into memory to validate and calculate hash
        content = await file.read()
        file_size = len(content)

        # 2. Validate file type and size
        try:
            self.pipeline.validate_file(file_name, file_size)
        except InvalidFileError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        content_hash = hashlib.sha256(content).hexdigest()

        # 3. Check for duplicates
        existing_doc = await self.doc_repo.get_by_content_hash(content_hash)
        if existing_doc and existing_doc.status != DocumentStatus.DELETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A document with identical content already exists: '{existing_doc.file_name}' (ID: {existing_doc.id})",
            )

        # 4. Save file to storage
        ext = os.path.splitext(file_name)[1].lower()
        unique_file_name = f"{uuid.uuid4()}{ext}"
        storage_path = os.path.join(settings.UPLOAD_DIR, unique_file_name)

        await asyncio.to_thread(_write_file_sync, storage_path, content)

        # 5. Create document record
        doc = await self.doc_repo.create_document(
            file_name=file_name,
            file_type=ext.lstrip("."),
            file_size=file_size,
            content_hash=content_hash,
            storage_path=storage_path,
            status=DocumentStatus.PENDING,
        )

        # 6. Run ingestion immediately (or schedule in background)
        try:
            doc = await self.pipeline.run(doc.id)
        except Exception as e:
            logger.error("Ingestion failed during upload", doc_id=str(doc.id), exc_info=e)

        return doc

    async def list_documents(
        self, skip: int = 0, limit: int = 50
    ) -> Sequence[Document]:
        return await self.doc_repo.list_documents(skip=skip, limit=limit)

    async def get_document(self, document_id: uuid.UUID) -> Optional[Document]:
        doc = await self.doc_repo.get_by_id(document_id)
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found",
            )
        return doc

    async def get_document_status(self, document_id: uuid.UUID) -> Document:
        return await self.get_document(document_id)

    async def delete_document(self, document_id: uuid.UUID) -> bool:
        doc = await self.get_document(document_id)
        if doc.status in (DocumentStatus.PROCESSING, DocumentStatus.INDEXING):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Cannot delete document while it is being processed.",
            )
        
        # Remove physical file if exists
        if os.path.exists(doc.storage_path):
            try:
                os.remove(doc.storage_path)
            except Exception as e:
                logger.warning("Could not delete physical file", path=doc.storage_path, error=str(e))

        return await self.doc_repo.delete_document(document_id)

    async def reprocess_document(self, document_id: uuid.UUID) -> Document:
        doc = await self.get_document(document_id)
        return await self.pipeline.run(document_id)
