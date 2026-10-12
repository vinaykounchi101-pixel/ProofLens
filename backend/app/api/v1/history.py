"""Saved query history and citation inspection endpoints (FR-12)."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.errors import ResourceNotFoundException
from app.models.query_history import QueryRun, Answer, Citation
from app.models.document import Document
from app.schemas.history import QueryHistoryItem, QueryHistoryDetail
from app.schemas.qa import CitationItem

router = APIRouter(prefix="/workspaces/{workspace_id}/history", tags=["history"])


@router.get("", response_model=List[QueryHistoryItem])
async def list_query_history(
    workspace_id: str,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(QueryRun)
        .options(selectinload(QueryRun.answer))
        .where(QueryRun.workspace_id == workspace_id)
        .order_by(QueryRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    runs = res.scalars().all()

    return [
        QueryHistoryItem(
            query_id=r.id,
            workspace_id=r.workspace_id,
            query_text=r.query_text,
            selected_doc_ids=r.selected_doc_ids or [],
            evidence_status=r.evidence_status,
            created_at=r.created_at,
            has_answer=r.answer is not None,
        )
        for r in runs
    ]


@router.get("/{query_id}", response_model=QueryHistoryDetail)
async def get_query_detail(
    workspace_id: str,
    query_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(QueryRun)
        .options(selectinload(QueryRun.answer).selectinload(Answer.citations))
        .where(QueryRun.id == query_id, QueryRun.workspace_id == workspace_id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Query run not found.")

    citation_items: List[CitationItem] = []
    answer_text = None
    latency_ms = None

    if run.answer:
        answer_text = run.answer.answer_text
        latency_ms = run.answer.latency_ms

        for cite in run.answer.citations:
            # Look up doc name
            doc_stmt = select(Document.original_filename).where(Document.id == run.selected_doc_ids[0])
            doc_res = await session.execute(doc_stmt)
            filename = doc_res.scalar_one_or_none() or "Document"

            citation_items.append(
                CitationItem(
                    citation_id=cite.id,
                    document_id=run.selected_doc_ids[0] if run.selected_doc_ids else "",
                    document_filename=filename,
                    page_number=cite.page_number,
                    cited_excerpt=cite.cited_excerpt,
                    is_verified=cite.is_verified,
                )
            )

    return QueryHistoryDetail(
        query_id=run.id,
        workspace_id=run.workspace_id,
        query_text=run.query_text,
        selected_doc_ids=run.selected_doc_ids or [],
        evidence_status=run.evidence_status,
        created_at=run.created_at,
        answer=answer_text,
        citations=citation_items,
        latency_ms=latency_ms,
    )
