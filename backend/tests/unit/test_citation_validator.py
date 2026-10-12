"""Unit tests for deterministic citation validation and evidence sufficiency (FR-07, FR-08)."""

from app.services.citation_service import citation_validator
from app.services.retrieval_service import RetrievedChunk


def test_validator_strips_hallucinated_citations():
    retrieved = [
        RetrievedChunk(
            chunk_id="chunk_1",
            document_id="doc_1",
            document_filename="Report.pdf",
            page_number=10,
            content="Revenue was 50 million.",
            similarity_score=0.92,
            rank=1,
        )
    ]
    label_map = {"E1": retrieved[0]}

    # LLM hallucinated E99
    llm_output = {
        "answer": "Revenue was 50 million and profit was high.",
        "claims": [
            {
                "claim_text": "Revenue was 50 million.",
                "cited_evidence_ids": ["E1"],
                "excerpt": "Revenue was 50 million.",
            },
            {
                "claim_text": "Profit was high.",
                "cited_evidence_ids": ["E99"],
                "excerpt": "Profit was high.",
            },
        ],
        "unsupported_aspects": None,
    }

    res = citation_validator.validate(llm_output, retrieved, label_map)
    # E99 should be stripped, so only E1 citation is validated
    assert len(res.validated_citations) == 1
    assert res.validated_citations[0].chunk_id == "chunk_1"
    assert res.validated_citations[0].page_number == 10
    # Because one claim was unsupported (E99 stripped), status must be partially_supported
    assert res.evidence_status == "partially_supported"


def test_validator_returns_insufficient_evidence_when_no_evidence():
    res = citation_validator.validate({"answer": "I don't know.", "claims": []}, [], {})
    assert res.evidence_status == "insufficient_evidence"
    assert len(res.validated_citations) == 0
