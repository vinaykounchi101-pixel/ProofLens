"""Document summary and suggested questions endpoints (FR-09)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.summary import DocumentSummaryResponse
from app.services.summary_service import summary_service

router = APIRouter(prefix="/workspaces/{workspace_id}/documents/{document_id}/summary", tags=["summaries"])


@router.get("", response_model=DocumentSummaryResponse)
async def get_summary(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    return await summary_service.get_or_generate_summary(
        session=session,
        workspace_id=workspace_id,
        document_id=document_id,
        force_regenerate=False,
    )


@router.post("", response_model=DocumentSummaryResponse)
async def regenerate_summary(
    workspace_id: str,
    document_id: str,
    session: AsyncSession = Depends(get_db),
):
    return await summary_service.get_or_generate_summary(
        session=session,
        workspace_id=workspace_id,
        document_id=document_id,
        force_regenerate=True,
    )
