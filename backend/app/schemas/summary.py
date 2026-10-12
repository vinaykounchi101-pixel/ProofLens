"""Document summary and suggested questions schemas (FR-09)."""

from typing import List, Optional
from pydantic import BaseModel


class DocumentSummaryResponse(BaseModel):
    document_id: str
    original_filename: str
    summary: Optional[str] = None
    suggested_questions: List[str] = []
    is_cached: bool = True
