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


class LiveQueryEvaluationItem(BaseModel):
    query_id: str
    question: str
    evidence_status: str
    answer_text: Optional[str] = None
    created_at: datetime
    latency_ms: Optional[int] = None
    total_citations: int = 0
    valid_citations: int = 0
    citation_validity_rate: float = 1.0
    has_hallucinations: bool = False
    is_abstention: bool = False


class LiveEvaluationSummary(BaseModel):
    workspace_id: str
    total_queries: int = 0
    supported_queries: int = 0
    abstention_queries: int = 0
    citation_validity_rate: float = 0.0
    abstention_rate: float = 0.0
    hallucination_rate: float = 0.0
    avg_latency_ms: float = 0.0
    evaluated_queries: List[LiveQueryEvaluationItem] = []

