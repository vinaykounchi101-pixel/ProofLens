"""Semantic vector retrieval service with workspace isolation (FR-05, FR-13)."""

import math
from typing import List, Dict, Any, NamedTuple
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import DocumentChunk
from app.models.document import Document
from app.core.config import settings


class RetrievedChunk(NamedTuple):
    chunk_id: str
    document_id: str
    document_filename: str
    page_number: int
    content: str
    similarity_score: float
    rank: int


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a)) or 1.0
    norm_b = math.sqrt(sum(b * b for b in vec_b)) or 1.0
    return dot / (norm_a * norm_b)


class RetrievalService:
    @staticmethod
    async def search(
        session: AsyncSession,
        workspace_id: str,
        document_ids: List[str],
        query_vector: List[float],
        top_k: int = 5,
        threshold: float = settings.RETRIEVAL_SIMILARITY_THRESHOLD,
    ) -> List[RetrievedChunk]:
        """
        Retrieves top-k candidate chunks strictly filtered by workspace_id and document_ids.
        Uses in-database vector similarity search (<=> cosine distance) on PostgreSQL/pgvector,
        and falls back to in-memory cosine similarity on SQLite.
        """
        if not document_ids or not query_vector:
            return []

        # Check database dialect
        bind = session.get_bind() if hasattr(session, "get_bind") else getattr(session, "bind", None)
        dialect_name = bind.dialect.name if bind else "sqlite"

        if dialect_name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                cos_dist = DocumentChunk.embedding.cosine_distance(query_vector)
                stmt = (
                    select(
                        DocumentChunk.id,
                        DocumentChunk.document_id,
                        DocumentChunk.page_number,
                        DocumentChunk.content,
                        Document.original_filename,
                        cos_dist.label("distance"),
                    )
                    .join(Document, DocumentChunk.document_id == Document.id)
                    .where(
                        and_(
                            DocumentChunk.workspace_id == workspace_id,
                            DocumentChunk.document_id.in_(document_ids),
                            Document.status == "indexed",
                            cos_dist <= (1.0 - threshold),
                        )
                    )
                    .order_by(cos_dist.asc())
                    .limit(top_k)
                )

                res = await session.execute(stmt)
                rows = res.all()

                return [
                    RetrievedChunk(
                        chunk_id=row[0],
                        document_id=row[1],
                        document_filename=row[4],
                        page_number=row[2],
                        content=row[3],
                        similarity_score=round(max(0.0, 1.0 - float(row[5])), 4),
                        rank=idx + 1,
                    )
                    for idx, row in enumerate(rows)
                ]
            except Exception:
                # If pgvector extension/column isn't configured in PostgreSQL, fallback to in-memory
                pass

        # SQLite / In-Memory Fallback
        stmt = (
            select(
                DocumentChunk.id,
                DocumentChunk.document_id,
                DocumentChunk.page_number,
                DocumentChunk.content,
                DocumentChunk.embedding,
                Document.original_filename,
            )
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(
                and_(
                    DocumentChunk.workspace_id == workspace_id,
                    DocumentChunk.document_id.in_(document_ids),
                    Document.status == "indexed",
                )
            )
        )

        res = await session.execute(stmt)
        rows = res.all()

        scored_candidates = []
        for row in rows:
            chunk_id, doc_id, page_num, content, emb, filename = row
            emb_list = list(emb) if hasattr(emb, "__iter__") else []
            if not emb_list:
                continue

            score = _cosine_similarity(query_vector, emb_list)
            if score >= threshold:
                scored_candidates.append({
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "document_filename": filename,
                    "page_number": page_num,
                    "content": content,
                    "score": score,
                })

        # Sort descending by similarity score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_candidates = scored_candidates[:top_k]

        return [
            RetrievedChunk(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                document_filename=c["document_filename"],
                page_number=c["page_number"],
                content=c["content"],
                similarity_score=round(c["score"], 4),
                rank=idx + 1,
            )
            for idx, c in enumerate(top_candidates)
        ]


retrieval_service = RetrievalService()
