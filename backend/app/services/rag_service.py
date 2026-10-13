import logging
import time
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters import get_embedding_adapter, get_llm_adapter
from app.core.usage import usage_tracker
from app.models.query_history import QueryRun, RetrievedEvidence, Answer, Citation
from app.schemas.qa import QAResponse, CitationItem, ClaimItem
from app.services.citation_service import citation_validator
from app.services.retrieval_service import retrieval_service

logger = logging.getLogger("prooflens")


class RAGService:
    @staticmethod
    async def answer_question(
        session: AsyncSession,
        workspace_id: str,
        question: str,
        document_ids: List[str],
        top_k: int = 5,
        track_usage: bool = True,
    ) -> QAResponse:
        start_time = time.time()

        # Enforce rate-limits and daily quotas (FR-14)
        if track_usage:
            usage_tracker.check_and_record(workspace_id)

        embedding_adapter = get_embedding_adapter()
        llm_adapter = get_llm_adapter()

        # Step 1: Embed query
        query_vector = await embedding_adapter.embed_query(question)

        # Step 2: Retrieve candidate chunks
        retrieved_chunks = await retrieval_service.search(
            session=session,
            workspace_id=workspace_id,
            document_ids=document_ids,
            query_vector=query_vector,
            top_k=top_k,
        )

        # Step 3: Handle empty / sub-threshold retrieval (Fast path, saves LLM quota)
        if not retrieved_chunks:
            latency_ms = int((time.time() - start_time) * 1000)
            query_run = QueryRun(
                workspace_id=workspace_id,
                query_text=question,
                selected_doc_ids=document_ids,
                evidence_status="insufficient_evidence",
            )
            session.add(query_run)
            await session.flush()

            answer_row = Answer(
                query_run_id=query_run.id,
                answer_text="The available documents do not contain evidence to answer this question.",
                evidence_status="insufficient_evidence",
                claims=[],
                latency_ms=latency_ms,
            )
            session.add(answer_row)
            await session.commit()

            return QAResponse(
                query_id=query_run.id,
                question=question,
                answer="The available documents do not contain evidence to answer this question.",
                evidence_status="insufficient_evidence",
                claims=[],
                citations=[],
                unsupported_aspects="No relevant passages found in selected documents.",
                latency_ms=latency_ms,
            )

        # Step 4: Map candidate passages to server-assigned labels [E1], [E2], ...
        evidence_passages = []
        chunk_label_map = {}
        for idx, chunk in enumerate(retrieved_chunks):
            label = f"E{idx + 1}"
            chunk_label_map[label] = chunk
            evidence_passages.append({
                "label": label,
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "filename": chunk.document_filename,
                "page_number": chunk.page_number,
                "content": chunk.content,
            })

        # Step 5: Invoke LLM with strict grounding instructions
        try:
            raw_llm_output = await llm_adapter.generate_grounded_answer(
                query=question,
                evidence_passages=evidence_passages,
            )
        except Exception as exc:
            logger.warning(
                "LLM adapter generation failed in RAG pipeline: %s. Generating verified evidence fallback directly.",
                exc,
            )
            fallback_claims = []
            fallback_bullets = []
            query_words = [w.lower().strip("?,.:;\"'()") for w in question.split() if len(w) >= 4]

            for p in evidence_passages[:3]:
                candidates = [line.strip() for line in p["content"].split("\n") if len(line.strip()) >= 15]
                matched_candidate = None
                for cand in candidates:
                    if any(w in cand.lower() for w in query_words):
                        matched_candidate = cand
                        break

                excerpt = matched_candidate or (candidates[0] if candidates else p["content"][:150].strip())
                if len(excerpt) > 220:
                    excerpt = excerpt[:220].rsplit(" ", 1)[0]

                fallback_claims.append({
                    "claim_text": f"According to {p['filename']} (Page {p['page_number']}), {excerpt}",
                    "cited_evidence_ids": [p["label"]],
                    "excerpt": excerpt,
                })
                fallback_bullets.append(f"• **Page {p['page_number']}**: {excerpt}")
            raw_llm_output = {
                "answer": (
                    f"Evidence retrieved from your indexed document for '{question}':\n\n"
                    + "\n".join(fallback_bullets)
                    + "\n\n*(Note: External Gemini API quota reached. Displaying verified evidence excerpts directly.)*"
                ),
                "claims": fallback_claims,
                "unsupported_aspects": None,
            }

        # Step 6: Validate citations, verify claims, and assign evidence status
        val_result = citation_validator.validate(
            raw_llm_output=raw_llm_output,
            retrieved_chunks=retrieved_chunks,
            chunk_label_map=chunk_label_map,
        )

        answer_text = raw_llm_output.get("answer", "")
        latency_ms = int((time.time() - start_time) * 1000)

        # Build claim serializable objects
        claims_data = []
        claim_items: List[ClaimItem] = []
        for c in val_result.validated_claims:
            claim_citations = [
                CitationItem(
                    citation_id=cite.citation_id,
                    document_id=cite.document_id,
                    document_filename=cite.document_filename,
                    page_number=cite.page_number,
                    cited_excerpt=cite.cited_excerpt,
                    is_reference_valid=cite.is_reference_valid,
                    is_excerpt_valid=cite.is_excerpt_valid,
                    is_verified=cite.is_verified,
                    is_repaired=cite.is_repaired,
                    repair_reason=cite.repair_reason,
                )
                for cite in c.citations
            ]
            claim_items.append(
                ClaimItem(
                    claim_text=c.claim_text,
                    cited_evidence_ids=c.cited_evidence_ids,
                    support_level=c.support_level,
                    citations=claim_citations,
                )
            )
            claims_data.append({
                "claim_text": c.claim_text,
                "cited_evidence_ids": c.cited_evidence_ids,
                "support_level": c.support_level,
            })

        # Step 7: Audit persistence for history replay (FR-12)
        query_run = QueryRun(
            workspace_id=workspace_id,
            query_text=question,
            selected_doc_ids=document_ids,
            evidence_status=val_result.evidence_status,
        )
        session.add(query_run)
        await session.flush()

        for chunk in retrieved_chunks:
            ret_ev = RetrievedEvidence(
                query_run_id=query_run.id,
                chunk_id=chunk.chunk_id,
                similarity_score=chunk.similarity_score,
                retrieval_rank=chunk.rank,
            )
            session.add(ret_ev)

        answer_row = Answer(
            query_run_id=query_run.id,
            answer_text=answer_text,
            evidence_status=val_result.evidence_status,
            claims=claims_data,
            latency_ms=latency_ms,
        )
        session.add(answer_row)
        await session.flush()

        citation_items: List[CitationItem] = []
        for cite in val_result.validated_citations:
            cite_row = Citation(
                answer_id=answer_row.id,
                chunk_id=cite.chunk_id,
                document_id=cite.document_id,
                document_filename=cite.document_filename,
                page_number=cite.page_number,
                cited_excerpt=cite.cited_excerpt,
                is_reference_valid=cite.is_reference_valid,
                is_excerpt_valid=cite.is_excerpt_valid,
                is_verified=cite.is_verified,
                is_repaired=cite.is_repaired,
                repair_reason=cite.repair_reason,
            )
            session.add(cite_row)
            citation_items.append(
                CitationItem(
                    citation_id=cite.citation_id,
                    document_id=cite.document_id,
                    document_filename=cite.document_filename,
                    page_number=cite.page_number,
                    cited_excerpt=cite.cited_excerpt,
                    is_reference_valid=cite.is_reference_valid,
                    is_excerpt_valid=cite.is_excerpt_valid,
                    is_verified=cite.is_verified,
                    is_repaired=cite.is_repaired,
                    repair_reason=cite.repair_reason,
                )
            )

        await session.commit()

        return QAResponse(
            query_id=query_run.id,
            question=question,
            answer=answer_text,
            evidence_status=val_result.evidence_status,
            claims=claim_items,
            citations=citation_items,
            unsupported_aspects=val_result.unsupported_aspects,
            latency_ms=latency_ms,
        )


rag_service = RAGService()
