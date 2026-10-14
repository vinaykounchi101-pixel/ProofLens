"""Deterministic server-side citation validation, claim support verification, and evidence sufficiency policy (FR-07, FR-08)."""

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
    is_reference_valid: bool
    is_excerpt_valid: bool
    is_verified: bool
    is_repaired: bool
    repair_reason: Optional[str]


class ValidatedClaim(NamedTuple):
    claim_text: str
    cited_evidence_ids: List[str]
    support_level: str  # supported, unsupported, contradicted, unverified
    citations: List[ValidatedCitation]


class ValidationResult(NamedTuple):
    evidence_status: str  # supported, partially_supported, conflicting_evidence, insufficient_evidence
    validated_claims: List[ValidatedClaim]
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
        Executes multi-stage deterministic verification:
        1. Reference Validity: Checks whether cited evidence IDs exist in the retrieved set.
        2. Excerpt Validity: Verifies that model excerpts genuinely exist within the source chunk.
           Does NOT falsely mark repaired/substituted excerpts as verified.
        3. Claim Support Verification: Assesses whether the claim is genuinely supported by cited text.
        4. Evidence Sufficiency & Conflict Classification.
        """
        if not retrieved_chunks:
            return ValidationResult(
                evidence_status="insufficient_evidence",
                validated_claims=[],
                validated_citations=[],
                unsupported_aspects="No relevant evidence passages found in authorized documents.",
            )

        if not isinstance(raw_llm_output, dict):
            if isinstance(raw_llm_output, list):
                raw_llm_output = {"claims": raw_llm_output, "answer": "", "unsupported_aspects": None}
            else:
                raw_llm_output = {"claims": [], "answer": str(raw_llm_output) if raw_llm_output else "", "unsupported_aspects": None}

        raw_claims = raw_llm_output.get("claims", [])
        unsupported = raw_llm_output.get("unsupported_aspects")
        answer_text = raw_llm_output.get("answer", "")

        # If model explicitly reported lack of information and provided zero claims
        if not raw_claims and unsupported:
            return ValidationResult(
                evidence_status="insufficient_evidence",
                validated_claims=[],
                validated_citations=[],
                unsupported_aspects=unsupported,
            )

        all_validated_citations: List[ValidatedCitation] = []
        validated_claims: List[ValidatedClaim] = []
        seen_chunks = set()

        for idx, claim in enumerate(raw_claims):
            claim_text = claim.get("claim_text", "").strip()
            cited_ids = claim.get("cited_evidence_ids", [])
            raw_excerpt = (claim.get("excerpt") or "").strip()

            claim_citations: List[ValidatedCitation] = []
            claim_has_valid_evidence = False
            claim_is_contradicted = False

            for cid in cited_ids:
                # Stage 1: Reference Validity
                if cid not in chunk_label_map:
                    # Nonexistent label (e.g. E99) or unretrieved document
                    continue

                chunk = chunk_label_map[cid]
                doc_id = chunk.document_id
                filename = chunk.document_filename
                page_num = chunk.page_number

                # Stage 2: Excerpt Validity
                norm_chunk_content = re.sub(r"\s+", " ", chunk.content).strip()
                norm_excerpt = re.sub(r"\s+", " ", raw_excerpt).strip()

                is_reference_valid = True
                is_excerpt_valid = False
                is_repaired = False
                repair_reason = None
                final_excerpt = ""

                # Check exact or case-insensitive sub-string containment
                if norm_excerpt and len(norm_excerpt) >= 8 and norm_excerpt.lower() in norm_chunk_content.lower():
                    is_excerpt_valid = True
                    final_excerpt = norm_excerpt
                else:
                    # Model provided fabricated excerpt or omitted excerpt
                    is_excerpt_valid = False
                    is_repaired = True
                    repair_reason = "fabricated_or_missing_excerpt"
                    # We preserve genuine chunk text as context, but DO NOT mark as verified
                    final_excerpt = chunk.content[:140].strip() + "..."

                # Stage 3: Claim Support
                # Check if evidence supports or contradicts claim
                claim_words = set(re.findall(r"\b\w{4,}\b", claim_text.lower()))
                chunk_words = set(re.findall(r"\b\w{4,}\b", norm_chunk_content.lower()))
                overlap = claim_words.intersection(chunk_words)

                # Check for explicit contradiction in text
                contradiction_markers = ["not required", "prohibited", "contrary", "differs from", "never", "cannot"]
                has_contradiction = any(m in norm_chunk_content.lower() and m not in claim_text.lower() for m in contradiction_markers)

                # A citation is strictly verified ONLY if:
                # 1. Reference is valid
                # 2. Excerpt is genuinely found in source (not repaired)
                # 3. Content overlaps meaningfully with claim
                # 4. No contradiction detected
                is_verified = is_reference_valid and is_excerpt_valid and len(overlap) >= 1 and not has_contradiction

                val_cite = ValidatedCitation(
                    citation_id=f"cit_{idx + 1}_{cid}",
                    chunk_id=chunk.chunk_id,
                    document_id=doc_id,
                    document_filename=filename,
                    page_number=page_num,
                    cited_excerpt=final_excerpt,
                    is_reference_valid=is_reference_valid,
                    is_excerpt_valid=is_excerpt_valid,
                    is_verified=is_verified,
                    is_repaired=is_repaired,
                    repair_reason=repair_reason,
                )

                claim_citations.append(val_cite)
                if is_verified:
                    claim_has_valid_evidence = True
                if has_contradiction:
                    claim_is_contradicted = True

                if chunk.chunk_id not in seen_chunks:
                    seen_chunks.add(chunk.chunk_id)
                    all_validated_citations.append(val_cite)

            # Assign Claim Support Level
            if claim_is_contradicted:
                support_level = "contradicted"
            elif claim_has_valid_evidence:
                support_level = "supported"
            elif claim_citations:
                support_level = "unverified"
            else:
                support_level = "unsupported"

            validated_claims.append(
                ValidatedClaim(
                    claim_text=claim_text,
                    cited_evidence_ids=cited_ids,
                    support_level=support_level,
                    citations=claim_citations,
                )
            )

        # Stage 4: Evidence Sufficiency & Overall Status Policy
        # Check for cross-document or claim contradictions
        has_contradicted_claims = any(c.support_level == "contradicted" for c in validated_claims)
        conflict_phrases = ["conflict", "disagree", "contradict", "differing terms", "discrepancy"]
        answer_mentions_conflict = any(w in answer_text.lower() for w in conflict_phrases)

        if has_contradicted_claims or (answer_mentions_conflict and len(set(c.document_id for c in all_validated_citations)) > 1):
            evidence_status = "conflicting_evidence"
        elif not all_validated_citations or all(c.support_level == "unsupported" for c in validated_claims):
            evidence_status = "insufficient_evidence"
        elif any(c.support_level in ["unsupported", "unverified"] for c in validated_claims) or unsupported:
            evidence_status = "partially_supported"
        elif all(c.support_level == "supported" for c in validated_claims):
            evidence_status = "supported"
        else:
            evidence_status = "partially_supported"

        return ValidationResult(
            evidence_status=evidence_status,
            validated_claims=validated_claims,
            validated_citations=all_validated_citations,
            unsupported_aspects=unsupported,
        )


citation_validator = CitationValidator()
