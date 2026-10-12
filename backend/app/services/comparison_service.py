"""Cross-document comparison service (FR-10)."""

from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters import get_embedding_adapter, get_llm_adapter
from app.core.errors import ValidationException
from app.models.comparison import ComparisonRun
from app.schemas.compare import CompareResponse, ComparisonFinding, DocumentSourceRef
from app.services.retrieval_service import retrieval_service


class ComparisonService:
    @staticmethod
    async def compare(
        session: AsyncSession,
        workspace_id: str,
        topic: str,
        document_ids: List[str],
    ) -> CompareResponse:
        if len(document_ids) < 2:
            raise ValidationException("At least two distinct documents are required for cross-document comparison.")

        embedding_adapter = get_embedding_adapter()
        llm_adapter = get_llm_adapter()

        query_vec = await embedding_adapter.embed_query(topic)

        # Independent retrieval per document to prevent starvation
        doc_a_id = document_ids[0]
        doc_b_id = document_ids[1]

        doc_a_chunks = await retrieval_service.search(
            session=session,
            workspace_id=workspace_id,
            document_ids=[doc_a_id],
            query_vector=query_vec,
            top_k=3,
        )

        doc_b_chunks = await retrieval_service.search(
            session=session,
            workspace_id=workspace_id,
            document_ids=[doc_b_id],
            query_vector=query_vec,
            top_k=3,
        )

        passages_a = [
            {"document_id": c.document_id, "filename": c.document_filename, "page_number": c.page_number, "content": c.content}
            for c in doc_a_chunks
        ]
        passages_b = [
            {"document_id": c.document_id, "filename": c.document_filename, "page_number": c.page_number, "content": c.content}
            for c in doc_b_chunks
        ]

        raw_comp = await llm_adapter.compare_documents(topic, passages_a, passages_b)

        findings_list: List[ComparisonFinding] = []
        for f in raw_comp.get("findings", []):
            doc_a_info = f.get("document_a")
            doc_b_info = f.get("document_b")

            ref_a = DocumentSourceRef(**doc_a_info) if doc_a_info else None
            ref_b = DocumentSourceRef(**doc_b_info) if doc_b_info else None

            findings_list.append(
                ComparisonFinding(
                    finding_type=f.get("finding_type", "agreement"),
                    topic_aspect=f.get("topic_aspect", topic),
                    description=f.get("description", ""),
                    document_a=ref_a,
                    document_b=ref_b,
                )
            )

        status = raw_comp.get("comparison_status", "completed")

        comp_run = ComparisonRun(
            workspace_id=workspace_id,
            topic=topic,
            target_doc_ids=document_ids,
            findings=[f.model_dump() for f in findings_list],
        )
        session.add(comp_run)
        await session.commit()

        return CompareResponse(
            comparison_id=comp_run.id,
            topic=topic,
            comparison_status=status,
            findings=findings_list,
        )


comparison_service = ComparisonService()
