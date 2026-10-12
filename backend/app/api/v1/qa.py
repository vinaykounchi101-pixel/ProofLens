"""Grounded Question Answering endpoint (FR-06, FR-07, FR-08)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.schemas.qa import QARequest, QAResponse
from app.services.rag_service import rag_service

router = APIRouter(prefix="/workspaces/{workspace_id}/qa", tags=["qa"])


@router.post("", response_model=QAResponse)
async def ask_question(
    workspace_id: str,
    payload: QARequest,
    session: AsyncSession = Depends(get_db),
):
    return await rag_service.answer_question(
        session=session,
        workspace_id=workspace_id,
        question=payload.question,
        document_ids=payload.document_ids,
        top_k=payload.top_k,
    )
