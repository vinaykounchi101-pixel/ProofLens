"""Comparison run ORM model for Cross-Document Comparison (FR-10)."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ComparisonRun(Base):
    __tablename__ = "comparison_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    workspace_id: Mapped[str] = mapped_column(String(36), ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    target_doc_ids: Mapped[list] = mapped_column(JSON, nullable=False)
    findings: Mapped[list] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    workspace = relationship("Workspace", back_populates="comparison_runs")
