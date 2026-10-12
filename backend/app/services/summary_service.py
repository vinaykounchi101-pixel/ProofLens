"""Document summary and suggested questions service (FR-09)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters import get_llm_adapter
from app.core.errors import ResourceNotFoundException
from app.models.document import Document
from app.models.chunk import DocumentChunk
from app.schemas.summary import DocumentSummaryResponse


class SummaryService:
    @staticmethod
    async def get_or_generate_summary(
        session: AsyncSession,
        workspace_id: str,
        document_id: str,
        force_regenerate: bool = False,
    ) -> DocumentSummaryResponse:
        stmt = select(Document).where(Document.id == document_id, Document.workspace_id == workspace_id)
        res = await session.execute(stmt)
        document = res.scalar_one_or_none()
        if not document:
            raise ResourceNotFoundException("Document not found in specified workspace.")

        # Return cached if available and not forced
        if not force_regenerate and document.summary and document.suggested_questions:
            return DocumentSummaryResponse(
                document_id=document.id,
                original_filename=document.original_filename,
                summary=document.summary,
                suggested_questions=document.suggested_questions,
                is_cached=True,
            )

        # Load first few chunks to form document sample
        chunk_stmt = (
            select(DocumentChunk.content)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index.asc())
            .limit(5)
        )
        chunk_res = await session.execute(chunk_stmt)
        sample_texts = chunk_res.scalars().all()
        combined_sample = "\n\n".join(sample_texts) if sample_texts else ""

        llm_adapter = get_llm_adapter()
        summary_data = await llm_adapter.generate_summary(combined_sample)

        document.summary = summary_data.get("summary")
        document.suggested_questions = summary_data.get("suggested_questions", [])
        await session.commit()

        return DocumentSummaryResponse(
            document_id=document.id,
            original_filename=document.original_filename,
            summary=document.summary,
            suggested_questions=document.suggested_questions or [],
            is_cached=False,
        )


summary_service = SummaryService()
