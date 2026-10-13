"""Mandatory Evaluation Integrity Tests (Section 6)."""

import pytest
from httpx import AsyncClient
from app.services.evaluation_service import evaluation_service
from app.models.evaluation import EvaluationRun, EvaluationResult
from app.core.database import async_session_factory


@pytest.mark.asyncio
async def test_unexecuted_workspace_returns_zero_metrics(async_client: AsyncClient):
    # Create empty workspace without any indexed documents
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Empty Evaluation Workspace", "description": "No documents uploaded"},
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    # Trigger evaluation
    eval_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/evaluation/run",
        json={"benchmark_name": "empty_test"},
    )
    assert eval_res.status_code == 200
    data = eval_res.json()

    # MUST report honest 0.0 metrics without fabricating scores
    metrics = data["metrics"]
    assert metrics["precision_at_k"] == 0.0
    assert metrics["recall_at_k"] == 0.0
    assert metrics["citation_validity_rate"] == 0.0
    assert metrics["abstention_accuracy"] == 0.0
    assert data["passed_cases"] == 0
    assert data["failed_cases"] > 0
    assert len(data["failed_results"]) > 0


@pytest.mark.asyncio
async def test_regression_metrics_dynamically_change(async_client: AsyncClient, sample_pdf_bytes: bytes):
    # Create workspace with real indexed document
    ws_res = await async_client.post(
        "/api/v1/workspaces",
        json={"name": "Active Benchmark Workspace", "description": "Real evaluation"},
    )
    assert ws_res.status_code == 201
    ws_id = ws_res.json()["id"]

    await async_client.post(
        f"/api/v1/workspaces/{ws_id}/documents/upload",
        files={"file": ("Benchmark_Doc.pdf", sample_pdf_bytes, "application/pdf")},
    )

    # Run benchmark
    run_res = await async_client.post(
        f"/api/v1/workspaces/{ws_id}/evaluation/run",
        json={"benchmark_name": "active_run"},
    )
    assert run_res.status_code == 200
    run_data = run_res.json()

    # Real metrics must be non-zero and computed from genuine test cases
    metrics = run_data["metrics"]
    assert metrics["citation_validity_rate"] > 0.0
    assert metrics["abstention_accuracy"] > 0.0
    assert run_data["total_cases"] == 25
    assert run_data["passed_cases"] > 0

    # Verify run is persisted in historical runs list
    list_res = await async_client.get(f"/api/v1/workspaces/{ws_id}/evaluation/runs")
    assert list_res.status_code == 200
    runs = list_res.json()
    assert len(runs) >= 1
    assert runs[0]["id"] == run_data["id"]
