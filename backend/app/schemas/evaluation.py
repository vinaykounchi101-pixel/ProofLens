"""Evaluation benchmark request and report schemas (FR-15)."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EvaluationRunRequest(BaseModel):
    benchmark_name: str = Field("mvp_baseline", description="Name of the evaluation benchmark run")


class EvaluationMetrics(BaseModel):
    precision_at_k: float = 0.0
    recall_at_k: float = 0.0
    citation_validity_rate: float = 0.0
    abstention_accuracy: float = 0.0


class EvaluationCaseResult(BaseModel):
    case_id: str
    passed: bool
    metrics: Dict[str, float] = {}
    failure_reason: Optional[str] = None


class EvaluationRunResponse(BaseModel):
    id: str
    benchmark_name: str
    total_cases: int
    passed_cases: int = 0
    failed_cases: int = 0
    metrics: EvaluationMetrics
    failed_results: List[EvaluationCaseResult] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
