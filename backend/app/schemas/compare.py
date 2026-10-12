"""Cross-document comparison request and finding schemas (FR-10)."""

from typing import List, Optional
from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    topic: str = Field(..., min_length=2, max_length=1000, description="The topic to compare across documents")
    document_ids: List[str] = Field(..., min_length=2, description="At least two document IDs are required for comparison")


class DocumentSourceRef(BaseModel):
    document_id: str
    document_filename: str
    page_number: int
    excerpt: str


class ComparisonFinding(BaseModel):
    finding_type: str  # agreement, contradiction, scope_difference, insufficient_evidence
    topic_aspect: str
    description: str
    document_a: Optional[DocumentSourceRef] = None
    document_b: Optional[DocumentSourceRef] = None


class CompareResponse(BaseModel):
    comparison_id: str
    topic: str
    comparison_status: str  # completed, insufficient_evidence
    findings: List[ComparisonFinding] = []
