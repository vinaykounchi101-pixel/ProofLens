"""Document request, response, and status schemas."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    workspace_id: str
    original_filename: str
    file_size_bytes: int
    total_pages: int
    total_chunks: int
    mime_type: str
    status: str  # uploaded, processing, indexed, failed, deleted
    error_message: Optional[str] = None
    summary: Optional[str] = None
    suggested_questions: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


class DocumentStatusResponse(BaseModel):
    document_id: str
    status: str
    total_pages: int
    total_chunks: int
    error_message: Optional[str] = None
