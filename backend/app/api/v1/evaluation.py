"""Evaluation benchmark endpoints (FR-15) with authorization."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_authorized_workspace, get_current_user
from app.core.errors import ResourceNotFoundException, ValidationException
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.workspace import Workspace
from app.models.user import User
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse, EvaluationMetrics, EvaluationCaseResult
from app.services.evaluation_service import evaluation_service

router = APIRouter(tags=["evaluation"])


@router.post("/workspaces/{workspace_id}/evaluation/run", response_model=EvaluationRunResponse)
async def run_workspace_benchmark(
    workspace_id: str,
    payload: Optional[EvaluationRunRequest] = None,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    benchmark_name = payload.benchmark_name if payload else "mvp_baseline"
    return await evaluation_service.run_evaluation(
        session=session,
        workspace_id=workspace.id,
        benchmark_name=benchmark_name,
    )


@router.post("/evaluation/run", response_model=EvaluationRunResponse)
async def run_evaluation_query_param(
    workspace_id: str = Query(...),
    payload: Optional[EvaluationRunRequest] = None,
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    workspace = await get_authorized_workspace(workspace_id=workspace_id, session=session, current_user=current_user)
    benchmark_name = payload.benchmark_name if payload else "mvp_baseline"
    return await evaluation_service.run_evaluation(
        session=session,
        workspace_id=workspace.id,
        benchmark_name=benchmark_name,
    )


@router.get("/workspaces/{workspace_id}/evaluation/runs", response_model=List[EvaluationRunResponse])
async def list_workspace_evaluation_runs(
    workspace_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.workspace_id == workspace.id)
        .order_by(EvaluationRun.created_at.desc())
    )
    res = await session.execute(stmt)
    runs = res.scalars().all()

    return [
        EvaluationRunResponse(
            id=r.id,
            benchmark_name=r.benchmark_name,
            metrics=EvaluationMetrics(
                precision_at_k=r.precision_at_k,
                recall_at_k=r.recall_at_k,
                citation_validity_rate=r.citation_validity_rate,
                abstention_accuracy=r.abstention_accuracy,
            ),
            total_cases=len(r.results),
            passed_cases=sum(1 for res_item in r.results if res_item.passed),
            failed_cases=sum(1 for res_item in r.results if not res_item.passed),
            failed_results=[
                EvaluationCaseResult(
                    case_id=res_item.case_id,
                    passed=res_item.passed,
                    metrics=res_item.metrics,
                    failure_reason=res_item.failure_reason,
                )
                for res_item in r.results
                if not res_item.passed
            ],
        )
        for r in runs
    ]


@router.get("/workspaces/{workspace_id}/evaluation/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_workspace_evaluation_run(
    workspace_id: str,
    run_id: str,
    workspace: Workspace = Depends(get_authorized_workspace),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == run_id, EvaluationRun.workspace_id == workspace.id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Evaluation run not found.")

    failed = [
        EvaluationCaseResult(
            case_id=res_item.case_id,
            passed=res_item.passed,
            metrics=res_item.metrics,
            failure_reason=res_item.failure_reason,
        )
        for res_item in run.results
        if not res_item.passed
    ]

    return EvaluationRunResponse(
        id=run.id,
        benchmark_name=run.benchmark_name,
        metrics=EvaluationMetrics(
            precision_at_k=run.precision_at_k,
            recall_at_k=run.recall_at_k,
            citation_validity_rate=run.citation_validity_rate,
            abstention_accuracy=run.abstention_accuracy,
        ),
        total_cases=len(run.results),
        passed_cases=len(run.results) - len(failed),
        failed_cases=len(failed),
        failed_results=failed,
    )


# Root endpoints for backward compatibility with integration tests
@router.post("/evaluation/run", response_model=EvaluationRunResponse)
async def run_benchmark_legacy(
    payload: EvaluationRunRequest,
    workspace_id: str = Query(..., description="Target authorized workspace ID"),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ws_stmt = select(Workspace).where(Workspace.id == workspace_id, Workspace.owner_id == current_user.id)
    ws_res = await session.execute(ws_stmt)
    ws = ws_res.scalar_one_or_none()
    if not ws:
        raise ResourceNotFoundException("Workspace not found.")

    return await evaluation_service.run_evaluation(
        session=session,
        workspace_id=ws.id,
        benchmark_name=payload.benchmark_name,
    )


@router.get("/evaluation/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run_legacy(
    run_id: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .join(Workspace, EvaluationRun.workspace_id == Workspace.id)
        .where(EvaluationRun.id == run_id, Workspace.owner_id == current_user.id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Evaluation run not found.")

    failed = [
        EvaluationCaseResult(
            case_id=res_item.case_id,
            passed=res_item.passed,
            metrics=res_item.metrics,
            failure_reason=res_item.failure_reason,
        )
        for res_item in run.results
        if not res_item.passed
    ]

    return EvaluationRunResponse(
        id=run.id,
        benchmark_name=run.benchmark_name,
        metrics=EvaluationMetrics(
            precision_at_k=run.precision_at_k,
            recall_at_k=run.recall_at_k,
            citation_validity_rate=run.citation_validity_rate,
            abstention_accuracy=run.abstention_accuracy,
        ),
        total_cases=len(run.results),
        passed_cases=len(run.results) - len(failed),
        failed_cases=len(failed),
        failed_results=failed,
    )
