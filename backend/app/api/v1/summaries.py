"""Document summary and suggested questions endpoints (FR-09) with authorization."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_document
from app.models.document import Document
from app.schemas.summary import DocumentSummaryResponse
from app.services.summary_service import summary_service

router = APIRouter(prefix="/workspaces/{workspace_id}/documents/{document_id}/summary", tags=["summaries"])


@router.get("", response_model=DocumentSummaryResponse)
async def get_summary(
    workspace_id: str,
    document_id: str,
    document: Document = Depends(get_authorized_document),
    session: AsyncSession = Depends(get_db),
):
    return await summary_service.get_or_generate_summary(
        session=session,
        workspace_id=workspace_id,
        document_id=document.id,
        force_regenerate=False,
    )


@router.post("", response_model=DocumentSummaryResponse)
async def regenerate_summary(
    workspace_id: str,
    document_id: str,
    document: Document = Depends(get_authorized_document),
    session: AsyncSession = Depends(get_db),
):
    return await summary_service.get_or_generate_summary(
        session=session,
        workspace_id=workspace_id,
        document_id=document.id,
        force_regenerate=True,
    )


from app.api.deps import get_db, get_authorized_document, get_authorized_document_by_id


standalone_summary_router = APIRouter(prefix="/documents/{document_id}/summary", tags=["summaries"])


@standalone_summary_router.get("", response_model=DocumentSummaryResponse)
async def get_summary_standalone(
    document: Document = Depends(get_authorized_document_by_id),
    session: AsyncSession = Depends(get_db),
):
    return await summary_service.get_or_generate_summary(
        session=session,
        workspace_id=document.workspace_id,
        document_id=document.id,
        force_regenerate=False,
    )

