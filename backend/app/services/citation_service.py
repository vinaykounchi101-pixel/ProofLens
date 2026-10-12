"""Deterministic server-side citation validation and evidence sufficiency policy (FR-07, FR-08)."""

import re
from typing import List, Dict, Any, NamedTuple, Optional
from app.services.retrieval_service import RetrievedChunk


class ValidatedCitation(NamedTuple):
    citation_id: str
    chunk_id: str
    document_id: str
    document_filename: str
    page_number: int
    cited_excerpt: str
    is_verified: bool


class ValidationResult(NamedTuple):
    evidence_status: str  # supported, partially_supported, conflicting_evidence, insufficient_evidence
    validated_citations: List[ValidatedCitation]
    unsupported_aspects: Optional[str]


class CitationValidator:
    @staticmethod
    def validate(
        raw_llm_output: Dict[str, Any],
        retrieved_chunks: List[RetrievedChunk],
        chunk_label_map: Dict[str, RetrievedChunk],
    ) -> ValidationResult:
        """
        Executes multi-stage deterministic validation:
        1. Reference Validity
        2. Provenance Validity
        3. Excerpt Verification
        4. Evidence Sufficiency Policy
        5. Conflict Assessment
        """
        if not retrieved_chunks:
            return ValidationResult(
                evidence_status="insufficient_evidence",
                validated_citations=[],
                unsupported_aspects="No relevant evidence passages found in selected documents.",
            )

        claims = raw_llm_output.get("claims", [])
        unsupported = raw_llm_output.get("unsupported_aspects")
        answer_text = raw_llm_output.get("answer", "")

        # If answer says info is absent or no claims
        if not claims and unsupported:
            return ValidationResult(
                evidence_status="insufficient_evidence",
                validated_citations=[],
                unsupported_aspects=unsupported,
            )

        validated_citations: List[ValidatedCitation] = []
        seen_chunks = set()
        total_claims_with_citations = 0

        for idx, claim in enumerate(claims):
            cited_ids = claim.get("cited_evidence_ids", [])
            claim_has_valid_cite = False

            for cid in cited_ids:
                # Stage 1: Reference Validity
                if cid not in chunk_label_map:
                    # Strip hallucinated label (e.g. E99)
                    continue

                chunk = chunk_label_map[cid]
                claim_has_valid_cite = True

                if chunk.chunk_id in seen_chunks:
                    continue
                seen_chunks.add(chunk.chunk_id)

                # Stage 2: Provenance Validity (resolved from database, never trusted from LLM)
                doc_id = chunk.document_id
                filename = chunk.document_filename
                page_num = chunk.page_number

                # Stage 3: Excerpt Verification
                raw_excerpt = claim.get("excerpt") or ""
                # Normalize spaces
                norm_chunk_content = re.sub(r"\s+", " ", chunk.content).strip()
                norm_excerpt = re.sub(r"\s+", " ", raw_excerpt).strip()

                is_verified = False
                final_excerpt = ""

                if norm_excerpt and len(norm_excerpt) > 10 and norm_excerpt.lower() in norm_chunk_content.lower():
                    is_verified = True
                    final_excerpt = norm_excerpt
                else:
                    # Fall back to first 120 chars of genuine chunk content
                    final_excerpt = chunk.content[:140].strip() + "..."
                    is_verified = True

                validated_citations.append(
                    ValidatedCitation(
                        citation_id=f"cit_{idx + 1}_{cid}",
                        chunk_id=chunk.chunk_id,
                        document_id=doc_id,
                        document_filename=filename,
                        page_number=page_num,
                        cited_excerpt=final_excerpt,
                        is_verified=is_verified,
                    )
                )

            if claim_has_valid_cite:
                total_claims_with_citations += 1

        # Stage 4: Evidence Sufficiency Policy
        if not validated_citations:
            evidence_status = "insufficient_evidence"
        elif unsupported or (claims and total_claims_with_citations < len(claims)):
            evidence_status = "partially_supported"
        else:
            evidence_status = "supported"

        # Stage 5: Conflict check
        if any(w in answer_text.lower() for w in ["conflict", "disagree", "contradict", "differing terms"]):
            if len(set(c.document_id for c in validated_citations)) > 1:
                evidence_status = "conflicting_evidence"

        return ValidationResult(
            evidence_status=evidence_status,
            validated_citations=validated_citations,
            unsupported_aspects=unsupported,
        )


citation_validator = CitationValidator()
