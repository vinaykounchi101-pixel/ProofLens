"""Document upload, status, retry, and library endpoints (FR-01, FR-02, FR-11, FR-13)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.errors import ResourceNotFoundException, ValidationException
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    force_reindex: bool = Query(False),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise ValidationException("Missing filename in uploaded file.")

    if not file.filename.lower().endswith(".pdf"):
        raise ValidationException("Only PDF files are supported in ProofLens AI.")

    content = await file.read()
    doc = await ingestion_service.ingest_document(
        session=session,
        workspace_id=workspace_id,
        original_filename=file.filename,
        file_bytes=content,
        force_reindex=force_reindex,
    )
    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    workspace_id: str,
    q: Optional[str] = Query(None, description="Search query by filename"),
    status: Optional[str] = Query(None, description="Filter by status (indexed, processing, failed)"),
    session: AsyncSession = Depends(get_db),
):
    conditions = [
        Document.workspace_id == workspace_id,
        Document.status != "deleted",
    ]
    if status:
        conditions.append(Document.status == status)
    if q:
        conditions.append(Document.original_filename.ilike(f"%{q}%"))

    stmt = select(Document).where(and_(*conditions)).order_by(Document.created_at.desc())
    res = await session.execute(stmt)
    return res.scalars().all()


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    res = await session.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document not found.")
    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
    res = await session.execute(stmt)
    doc = res.scalar_one_or_none()
    if not doc:
        raise ResourceNotFoundException("Document not found.")
    return DocumentStatusResponse(
        document_id=doc.id,
        status=doc.status,
        total_pages=doc.total_pages,
        total_chunks=doc.total_chunks,
        error_message=doc.error_message,
    )


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_ingestion(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    doc = await ingestion_service.retry_document(session, workspace_id, document_id)
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    await ingestion_service.delete_document(session, workspace_id, document_id)
