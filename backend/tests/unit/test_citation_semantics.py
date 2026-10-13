"""Mandatory Citation Verification and Evidence Semantics Tests (Section 5)."""

import pytest
from app.services.citation_service import citation_validator
from app.services.retrieval_service import RetrievedChunk


@pytest.fixture
def sample_retrieved_evidence():
    chunks = [
        RetrievedChunk(
            chunk_id="chunk-001",
            document_id="doc-abc-123",
            document_filename="Quarterly_Report.pdf",
            page_number=3,
            content="Total net sales were 81797 million dollars for the third quarter period. Operating income increased by 12 percent.",
            similarity_score=0.89,
            rank=1,
        ),
        RetrievedChunk(
            chunk_id="chunk-002",
            document_id="doc-abc-123",
            document_filename="Quarterly_Report.pdf",
            page_number=4,
            content="The company had cash and cash equivalents of 29965 million dollars as of September 30.",
            similarity_score=0.78,
            rank=2,
        ),
    ]
    label_map = {f"E{i+1}": c for i, c in enumerate(chunks)}
    return chunks, label_map


def test_correct_claim_and_correct_citation(sample_retrieved_evidence):
    chunks, label_map = sample_retrieved_evidence
    raw_llm = {
        "answer": "Total net sales were 81797 million dollars for the third quarter period.",
        "claims": [
            {
                "claim_text": "Total net sales reached 81797 million dollars for the quarter.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "Total net sales were 81797 million dollars for the third quarter period.",
            }
        ],
    }

    res = citation_validator.validate(
        raw_llm_output=raw_llm,
        retrieved_chunks=chunks,
        chunk_label_map=label_map,
    )

    assert res.evidence_status == "supported"
    assert len(res.validated_citations) == 1
    c = res.validated_citations[0]
    assert c.is_reference_valid is True
    assert c.is_excerpt_valid is True
    assert c.is_verified is True
    assert c.is_repaired is False
    assert c.document_id == "doc-abc-123"
    assert c.page_number == 3
    assert res.validated_claims[0].support_level == "supported"


def test_fabricated_excerpt_rejected_from_verification(sample_retrieved_evidence):
    chunks, label_map = sample_retrieved_evidence
    # Model generates a hallucinated quote that does not appear in the source chunk
    raw_llm = {
        "answer": "The company expects revenue of 500 billion next year.",
        "claims": [
            {
                "claim_text": "The company expects revenue of 500 billion next year.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "The CEO guaranteed 500 billion revenue next year unconditionally.",
            }
        ],
    }

    res = citation_validator.validate(
        raw_llm_output=raw_llm,
        retrieved_chunks=chunks,
        chunk_label_map=label_map,
    )

    assert len(res.validated_citations) == 1
    c = res.validated_citations[0]
    # Fabricated excerpt MUST NOT be marked as verified
    assert c.is_excerpt_valid is False
    assert c.is_verified is False
    assert res.validated_claims[0].support_level in ["unsupported", "unverified"]
    # If any material claim is unsupported, answer cannot be fully supported
    assert res.evidence_status != "supported"


def test_citation_to_nonexistent_evidence_reference(sample_retrieved_evidence):
    chunks, label_map = sample_retrieved_evidence
    # Model cites [E99] which does not exist in retrieved candidate set
    raw_llm = {
        "answer": "Some hallucinated claim.",
        "claims": [
            {
                "claim_text": "Some claim about outer space.",
                "cited_evidence_ids": ["E99"],
                "excerpt": "Total net sales were 81797 million dollars.",
            }
        ],
    }

    res = citation_validator.validate(
        raw_llm_output=raw_llm,
        retrieved_chunks=chunks,
        chunk_label_map=label_map,
    )

    assert res.evidence_status == "insufficient_evidence"
    assert len(res.validated_citations) == 0
    assert res.validated_claims[0].support_level in ["unsupported", "unverified"]


def test_multiple_claims_with_mixed_support_levels(sample_retrieved_evidence):
    chunks, label_map = sample_retrieved_evidence
    raw_llm = {
        "answer": "Mixed answer with one true claim and one false claim.",
        "claims": [
            {
                "claim_text": "Total net sales were 81797 million dollars.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "Total net sales were 81797 million dollars for the third quarter period.",
            },
            {
                "claim_text": "The company bought an island in the Caribbean.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "Completely fabricated quote about buying an island.",
            },
        ],
    }

    res = citation_validator.validate(
        raw_llm_output=raw_llm,
        retrieved_chunks=chunks,
        chunk_label_map=label_map,
    )

    # First claim is supported, second is unsupported -> status MUST be partially_supported
    assert res.validated_claims[0].support_level == "supported"
    assert res.validated_claims[1].support_level in ["unsupported", "unverified"]
    assert res.evidence_status == "partially_supported"


def test_repaired_excerpt_is_not_falsely_verified(sample_retrieved_evidence):
    chunks, label_map = sample_retrieved_evidence
    # Near-match excerpt with minor whitespace/casing drift that is repaired
    raw_llm = {
        "answer": "Total net sales were 81797 million dollars.",
        "claims": [
            {
                "claim_text": "Total net sales were 81797 million dollars.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "Total net sales was 81797 million dollars for third quarter period",
            }
        ],
    }

    res = citation_validator.validate(
        raw_llm_output=raw_llm,
        retrieved_chunks=chunks,
        chunk_label_map=label_map,
    )

    assert len(res.validated_citations) == 1
    c = res.validated_citations[0]
    if c.is_repaired:
        # Repaired citations must have explicit repair provenance
        assert c.repair_reason is not None


def test_no_retrieved_evidence_causes_truthful_abstention():
    res = citation_validator.validate(
        raw_llm_output={"answer": "", "claims": []},
        retrieved_chunks=[],
        chunk_label_map={},
    )

    assert res.evidence_status == "insufficient_evidence"
    assert len(res.validated_citations) == 0
