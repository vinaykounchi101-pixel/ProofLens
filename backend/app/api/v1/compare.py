"""Cross-document comparison endpoint (FR-10)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.comparison_service import comparison_service

router = APIRouter(prefix="/workspaces/{workspace_id}/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
async def compare_documents(
    workspace_id: str,
    payload: CompareRequest,
    session: AsyncSession = Depends(get_db),
):
    return await comparison_service.compare(
        session=session,
        workspace_id=workspace_id,
        topic=payload.topic,
        document_ids=payload.document_ids,
    )
