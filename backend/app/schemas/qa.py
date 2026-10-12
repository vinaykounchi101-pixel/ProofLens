"""Grounded Q&A request and response schemas (FR-06, FR-07, FR-08)."""

from typing import List, Optional
from pydantic import BaseModel, Field


class QARequest(BaseModel):
    question: str = Field(..., min_length=2, max_length=2000, description="The user question to answer from documents")
    document_ids: List[str] = Field(..., min_length=1, description="List of document IDs within the authorized workspace")
    top_k: int = Field(5, ge=1, le=20, description="Maximum number of evidence chunks to retrieve")


class CitationItem(BaseModel):
    citation_id: str
    document_id: str
    document_filename: str
    page_number: int
    cited_excerpt: str
    is_verified: bool = True


class QAResponse(BaseModel):
    query_id: str
    question: str
    answer: str
    evidence_status: str  # supported, partially_supported, conflicting_evidence, insufficient_evidence
    citations: List[CitationItem] = []
    unsupported_aspects: Optional[str] = None
    latency_ms: int = 0
