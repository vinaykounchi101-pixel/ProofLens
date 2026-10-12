"""Workspace ORM model."""

import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    documents = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    chunks = relationship("DocumentChunk", back_populates="workspace", cascade="all, delete-orphan")
    query_runs = relationship("QueryRun", back_populates="workspace", cascade="all, delete-orphan")
    comparison_runs = relationship("ComparisonRun", back_populates="workspace", cascade="all, delete-orphan")
