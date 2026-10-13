"""Grounded Question Answering endpoint (FR-06, FR-07, FR-08) with authorization."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_workspace
from app.core.errors import ResourceNotFoundException, ValidationException
from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.qa import QARequest, QAResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/workspaces/{workspace_id}/qa", tags=["qa"])


@router.post("", response_model=QAResponse)
async def ask_question(
    workspace_id: str,
    payload: QARequest,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    if not payload.document_ids:
        raise ValidationException("At least one document ID must be specified.")

    # Strictly verify that all target document IDs belong to this authorized workspace
    stmt = select(Document.id).where(
        Document.workspace_id == workspace.id,
        Document.id.in_(payload.document_ids),
        Document.status == "indexed",
    )
    res = await session.execute(stmt)
    authorized_doc_ids = set(res.scalars().all())

    # If any requested document is not authorized or not indexed, fail closed
    for doc_id in payload.document_ids:
        if doc_id not in authorized_doc_ids:
            raise ResourceNotFoundException(f"Document '{doc_id}' not found or not indexed in this workspace.")

    return await rag_service.answer_question(
        session=session,
        workspace_id=workspace.id,
        question=payload.question,
        document_ids=list(authorized_doc_ids),
        top_k=payload.top_k,
    )
