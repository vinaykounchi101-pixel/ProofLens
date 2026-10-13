"""Document upload, status, retry, and library endpoints (FR-01, FR-02, FR-11, FR-13)."""

from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_workspace, get_authorized_document
from app.core.config import settings
from app.core.errors import ResourceNotFoundException, ValidationException
from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.services.ingestion_service import ingestion_service

router = APIRouter(prefix="/workspaces/{workspace_id}/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    workspace_id: str,
    file: UploadFile = File(...),
    force_reindex: bool = Query(False),
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise ValidationException("Missing filename in uploaded file.")

    clean_name = file.filename.strip()
    if not clean_name.lower().endswith(".pdf"):
        raise ValidationException("Only PDF files are supported in ProofLens AI.")

    # Bounded streaming read to enforce MAX_UPLOAD_SIZE_BYTES without uncontrolled memory spikes
    chunk_size = 1024 * 64  # 64 KB
    max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
    bytes_read = 0
    chunks = []

    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        bytes_read += len(chunk)
        if bytes_read > max_bytes:
            raise ValidationException(
                f"File size exceeds maximum permitted limit of {max_bytes // (1024 * 1024)} MB.",
                details={"max_bytes": max_bytes, "bytes_received": bytes_read},
            )
        chunks.append(chunk)

    content = b"".join(chunks)
    if len(content) == 0:
        raise ValidationException("Uploaded PDF file is empty (0 bytes).")

    if not content.startswith(b"%PDF-"):
        raise ValidationException("File does not contain a valid PDF signature (%PDF-).")

    doc = await ingestion_service.ingest_document(
        session=session,
        workspace_id=workspace.id,
        original_filename=clean_name,
        file_bytes=content,
        force_reindex=force_reindex,
    )
    return doc


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    workspace_id: str,
    q: Optional[str] = Query(None, description="Search query by filename"),
    status: Optional[str] = Query(None, description="Filter by status (indexed, processing, failed)"),
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    conditions = [
        Document.workspace_id == workspace.id,
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
    document: Document = Depends(get_authorized_document),
):
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document: Document = Depends(get_authorized_document),
):
    return DocumentStatusResponse(
        document_id=document.id,
        status=document.status,
        total_pages=document.total_pages,
        total_chunks=document.total_chunks,
        error_message=document.error_message,
    )


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_ingestion(
    workspace_id: str,
    document_id: str,
    document: Document = Depends(get_authorized_document),
    session: AsyncSession = Depends(get_db),
):
    doc = await ingestion_service.retry_document(session, workspace_id, document_id)
    return doc


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    workspace_id: str,
    document_id: str,
    document: Document = Depends(get_authorized_document),
    session: AsyncSession = Depends(get_db),
):
    await ingestion_service.delete_document(session, workspace_id, document_id)


from app.api.deps import get_db, get_authorized_workspace, get_authorized_document, get_authorized_document_by_id


standalone_router = APIRouter(prefix="/documents", tags=["documents"])


@standalone_router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_standalone(
    document: Document = Depends(get_authorized_document_by_id),
):
    return document


@standalone_router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document_standalone(
    document: Document = Depends(get_authorized_document_by_id),
    session: AsyncSession = Depends(get_db),
):
    await ingestion_service.delete_document(session, document.workspace_id, document.id)


@standalone_router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_standalone(
    document: Document = Depends(get_authorized_document_by_id),
    session: AsyncSession = Depends(get_db),
):
    return await ingestion_service.retry_document(session, document.workspace_id, document.id)

