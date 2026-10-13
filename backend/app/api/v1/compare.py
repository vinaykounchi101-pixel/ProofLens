"""Cross-document comparison endpoint (FR-10) with authorization."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_workspace
from app.core.errors import ResourceNotFoundException, ValidationException
from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.compare import CompareRequest, CompareResponse
from app.services.comparison_service import comparison_service

router = APIRouter(prefix="/workspaces/{workspace_id}/compare", tags=["compare"])


@router.post("", response_model=CompareResponse)
async def compare_documents(
    workspace_id: str,
    payload: CompareRequest,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    if len(payload.document_ids) < 2:
        raise ValidationException("At least two distinct document IDs are required for cross-document comparison.")

    # Strictly verify that all target document IDs belong to this authorized workspace
    stmt = select(Document.id).where(
        Document.workspace_id == workspace.id,
        Document.id.in_(payload.document_ids),
        Document.status == "indexed",
    )
    res = await session.execute(stmt)
    authorized_doc_ids = set(res.scalars().all())

    for doc_id in payload.document_ids:
        if doc_id not in authorized_doc_ids:
            raise ResourceNotFoundException(f"Document '{doc_id}' not found or not indexed in this workspace.")

    return await comparison_service.compare(
        session=session,
        workspace_id=workspace.id,
        topic=payload.topic,
        document_ids=payload.document_ids,
    )
