"""Evaluation benchmark endpoints (FR-15)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.core.errors import ResourceNotFoundException
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.models.workspace import Workspace
from app.schemas.evaluation import EvaluationRunRequest, EvaluationRunResponse, EvaluationMetrics, EvaluationCaseResult
from app.services.evaluation_service import evaluation_service

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.post("/run", response_model=EvaluationRunResponse)
async def run_benchmark(
    payload: EvaluationRunRequest,
    workspace_id: str = Query(None, description="Optional workspace to run against"),
    session: AsyncSession = Depends(get_db),
):
    ws_id = workspace_id
    if not ws_id:
        # Fetch or create a default evaluation workspace
        ws_stmt = select(Workspace).limit(1)
        ws_res = await session.execute(ws_stmt)
        ws = ws_res.scalar_one_or_none()
        if ws:
            ws_id = ws.id
        else:
            new_ws = Workspace(name="Evaluation Workspace", description="Automated benchmark workspace")
            session.add(new_ws)
            await session.commit()
            ws_id = new_ws.id

    return await evaluation_service.run_evaluation(
        session=session,
        workspace_id=ws_id,
        benchmark_name=payload.benchmark_name,
    )


@router.get("/runs/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation_run(
    run_id: str,
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(EvaluationRun)
        .options(selectinload(EvaluationRun.results))
        .where(EvaluationRun.id == run_id)
    )
    res = await session.execute(stmt)
    run = res.scalar_one_or_none()
    if not run:
        raise ResourceNotFoundException("Evaluation run not found.")

    failed = [
        EvaluationCaseResult(
            case_id=r.case_id,
            passed=r.passed,
            metrics=r.metrics or {},
            failure_reason=r.failure_reason,
        )
        for r in run.results
        if not r.passed
    ]

    metrics = EvaluationMetrics(
        precision_at_k=run.precision_at_k,
        recall_at_k=run.recall_at_k,
        citation_validity_rate=run.citation_validity_rate,
        abstention_accuracy=run.abstention_accuracy,
    )

    return EvaluationRunResponse(
        run_id=run.id,
        benchmark_name=run.benchmark_name,
        total_cases=len(run.results),
        metrics=metrics,
        failed_cases=failed,
        created_at=run.created_at,
    )
