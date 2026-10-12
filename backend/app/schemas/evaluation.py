"""Evaluation benchmark request and report schemas (FR-15)."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel


class EvaluationRunRequest(BaseModel):
    benchmark_name: str = "mvp_baseline"


class EvaluationMetrics(BaseModel):
    precision_at_k: float
    recall_at_k: float
    citation_validity_rate: float
    abstention_accuracy: float


class EvaluationCaseResult(BaseModel):
    case_id: str
    passed: bool
    metrics: Dict[str, float]
    failure_reason: Optional[str] = None


class EvaluationRunResponse(BaseModel):
    run_id: str
    benchmark_name: str
    total_cases: int
    metrics: EvaluationMetrics
    failed_cases: List[EvaluationCaseResult] = []
    created_at: datetime
