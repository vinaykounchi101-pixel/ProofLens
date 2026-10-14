"""Saved query history and citation inspection endpoints (FR-12) with multi-document provenance and authorization."""

from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_workspace
from app.core.errors import ResourceNotFoundException
from app.models.query_history import QueryRun, Answer, Citation
from app.models.workspace import Workspace
from app.models.document import Document
from app.schemas.history import QueryHistoryItem, QueryHistoryDetail, QuerySaveResponse
from app.schemas.qa import CitationItem, ClaimItem

router = APIRouter(prefix="/workspaces/{workspace_id}/history", tags=["history"])


@router.get("", response_model=List[QueryHistoryItem])
async def list_query_history(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(QueryRun)
        .options(selectinload(QueryRun.answer).selectinload(Answer.citations))
        .where(QueryRun.workspace_id == workspace.id)
        .order_by(QueryRun.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    res = await session.execute(stmt)
    runs = res.scalars().all()

    items = []
    for r in runs:
        citation_items = []
        answer_text = None
        if r.answer:
            answer_text = r.answer.answer_text
            for c in r.answer.citations:
                citation_items.append(
                    CitationItem(
                        citation_id=c.id,
                        document_id=c.document_id,
                        document_filename=c.document_filename or "Document",
                        page_number=c.page_number,
                        cited_excerpt=c.cited_excerpt,
                        is_reference_valid=c.is_reference_valid,
                        is_excerpt_valid=c.is_excerpt_valid,
                        is_verified=c.is_verified,
                        is_repaired=c.is_repaired,
                        repair_reason=c.repair_reason,
                    )
                )

        items.append(
            QueryHistoryItem(
                query_id=r.id,
                id=r.id,
                workspace_id=r.workspace_id,
                query_text=r.query_text,
                question=r.query_text,
                selected_doc_ids=r.selected_doc_ids or [],
                evidence_status=r.evidence_status,
                created_at=r.created_at,
                has_answer=r.answer is not None,
                answer_text=answer_text,
                citations=citation_items,
                is_saved=getattr(r, "is_saved", True),
            )
        )

    return items


@router.get("/{query_id}", response_model=QueryHistoryDetail)
async def get_query_detail(
    workspace_id: str,
    query_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(QueryRun)
        .options(selectinload(QueryRun.answer).selectinload(Answer.citations))
        .where(QueryRun.id == query_id, QueryRun.workspace_id == workspace.id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Query run not found.")

    citation_items: List[CitationItem] = []
    claim_items: List[ClaimItem] = []
    answer_text = None
    latency_ms = None

    if run.answer:
        answer_text = run.answer.answer_text
        latency_ms = run.answer.latency_ms

        if run.answer.claims:
            claim_items = [
                ClaimItem(
                    claim_text=c.get("claim_text", ""),
                    cited_evidence_ids=c.get("cited_evidence_ids", []),
                    support_level=c.get("support_level", "supported"),
                )
                for c in run.answer.claims
            ]

        # Fetch all active documents for this workspace in one query to check status
        doc_stmt = select(Document.id, Document.original_filename, Document.status).where(
            Document.workspace_id == workspace.id
        )
        doc_res = await session.execute(doc_stmt)
        active_docs = {row[0]: (row[1], row[2]) for row in doc_res.all()}

        for cite in run.answer.citations:
            doc_info = active_docs.get(cite.document_id)
            if doc_info:
                doc_name = doc_info[0]
                if doc_info[1] == "deleted":
                    doc_name = f"{doc_name} (deleted)"
            else:
                doc_name = cite.document_filename or "Document (removed)"

            citation_items.append(
                CitationItem(
                    citation_id=cite.id,
                    document_id=cite.document_id,
                    document_filename=doc_name,
                    page_number=cite.page_number,
                    cited_excerpt=cite.cited_excerpt,
                    is_reference_valid=cite.is_reference_valid,
                    is_excerpt_valid=cite.is_excerpt_valid,
                    is_verified=cite.is_verified,
                    is_repaired=cite.is_repaired,
                    repair_reason=cite.repair_reason,
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
        claims=claim_items,
        citations=citation_items,
        latency_ms=latency_ms,
    )


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_query_run(
    workspace_id: str,
    query_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    """Delete an individual query run and its associated answer and citations from history."""
    stmt = select(QueryRun).where(QueryRun.id == query_id, QueryRun.workspace_id == workspace.id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Query run not found.")
    await session.delete(run)
    await session.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_workspace_history(
    workspace_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    """Clear all query history in the specified workspace."""
    stmt = select(QueryRun).where(QueryRun.workspace_id == workspace.id)
    res = await session.execute(stmt)
    runs = res.scalars().all()
    for r in runs:
        await session.delete(r)
    await session.commit()


@router.post("/{query_id}/save", response_model=QuerySaveResponse)
async def toggle_save_query_run(
    workspace_id: str,
    query_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    """Toggle or set the saved bookmark status of a query run."""
    stmt = select(QueryRun).where(QueryRun.id == query_id, QueryRun.workspace_id == workspace.id)
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Query run not found.")
    run.is_saved = not getattr(run, "is_saved", True)
    await session.commit()
    return QuerySaveResponse(query_id=run.id, is_saved=run.is_saved)

