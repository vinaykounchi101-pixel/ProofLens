"""Query run history and citation replay schemas (FR-12)."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.qa import CitationItem, ClaimItem


class QueryHistoryItem(BaseModel):
    query_id: str
    id: Optional[str] = None
    workspace_id: str
    query_text: str
    question: Optional[str] = None
    selected_doc_ids: List[str]
    evidence_status: str
    created_at: datetime
    has_answer: bool
    answer_text: Optional[str] = None
    citations: List[CitationItem] = []
    is_saved: bool = True


class QuerySaveResponse(BaseModel):
    query_id: str
    is_saved: bool


class QueryHistoryDetail(BaseModel):
    query_id: str
    workspace_id: str
    query_text: str
    selected_doc_ids: List[str]
    evidence_status: str
    created_at: datetime
    answer: Optional[str] = None
    claims: List[ClaimItem] = []
    citations: List[CitationItem] = []
    latency_ms: Optional[int] = None
