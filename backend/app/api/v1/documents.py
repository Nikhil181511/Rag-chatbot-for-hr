import uuid
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.services.document_service import DocumentService
from app.api.deps import require_hr, require_employee_or_hr
from app.models.user import User
from app.schemas.document import (
    DocumentItem,
    DocumentUploadItem,
    DocumentUploadResponse,
    DocumentListResponse,
    DocumentStatusResponse,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_documents(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    service = DocumentService(db)
    uploaded_items: List[DocumentUploadItem] = []

    for file in files:
        doc = await service.upload_document(file)
        uploaded_items.append(
            DocumentUploadItem(
                id=doc.id,
                file_name=doc.file_name,
                status=doc.status,
                file_size=doc.file_size,
            )
        )

    return DocumentUploadResponse(documents=uploaded_items)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_employee_or_hr),
):
    service = DocumentService(db)
    docs = await service.list_documents(skip=skip, limit=limit)
    items = []
    for d in docs:
        chunk_count = sum(len(v.chunks) for v in d.versions) if d.versions else 0
        items.append(
            DocumentItem(
                id=d.id,
                file_name=d.file_name,
                file_type=d.file_type,
                file_size=d.file_size,
                status=d.status,
                title=d.title,
                document_category=d.document_category,
                chunk_count=chunk_count,
                error_message=d.error_message,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
        )
    return DocumentListResponse(documents=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentItem)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    d = await service.get_document(document_id)
    chunk_count = sum(len(v.chunks) for v in d.versions) if d.versions else 0
    return DocumentItem(
        id=d.id,
        file_name=d.file_name,
        file_type=d.file_type,
        file_size=d.file_size,
        status=d.status,
        title=d.title,
        document_category=d.document_category,
        chunk_count=chunk_count,
        error_message=d.error_message,
        created_at=d.created_at,
        updated_at=d.updated_at,
    )


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    service = DocumentService(db)
    doc = await service.get_document_status(document_id)
    return DocumentStatusResponse(
        id=doc.id,
        status=doc.status,
        error_message=doc.error_message,
        updated_at=doc.updated_at,
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    service = DocumentService(db)
    await service.delete_document(document_id)
    return None


@router.post("/{document_id}/reprocess", status_code=status.HTTP_202_ACCEPTED)
async def reprocess_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_hr),
):
    service = DocumentService(db)
    doc = await service.reprocess_document(document_id)
    return {"id": doc.id, "status": doc.status}
