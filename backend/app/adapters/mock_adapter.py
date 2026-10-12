"""Deterministic offline mock provider adapter for reproducible local testing (FR-15, NFR)."""

import hashlib
import math
from typing import List, Dict, Any, Optional
from app.adapters.base import EmbeddingAdapter, LLMAdapter


def _text_to_deterministic_vector(text: str, dim: int = 768) -> List[float]:
    """Generates a deterministic, normalized 768-dimensional vector from text."""
    # Hash the text into 32-byte chunks
    seed = hashlib.sha256(text.encode("utf-8")).digest()
    vec = []
    for i in range(dim):
        byte_val = seed[i % len(seed)]
        # Map to range [-1.0, 1.0]
        val = (byte_val / 127.5) - 1.0
        # Add word frequency signal so similar texts have higher cosine similarity
        words = text.lower().split()
        for w in words[:5]:
            val += (sum(ord(c) for c in w) % 10) * 0.05
        vec.append(val)

    # Normalize to unit length
    magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / magnitude for x in vec]


class MockEmbeddingAdapter(EmbeddingAdapter):
    def __init__(self, dim: int = 768):
        self.dim = dim

    async def embed_query(self, query: str) -> List[float]:
        return _text_to_deterministic_vector(query, self.dim)

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [_text_to_deterministic_vector(t, self.dim) for t in texts]


class MockLLMAdapter(LLMAdapter):
    async def generate_grounded_answer(
        self,
        query: str,
        evidence_passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Out-of-corpus / unanswerable detection:
        if not evidence_passages:
            return {
                "answer": "The available documents do not contain evidence to answer this question.",
                "claims": [],
                "unsupported_aspects": "Evidence absent from corpus.",
            }

        # Check if query is looking for information absent from the evidence
        query_lower = query.lower()
        if "itinerary" in query_lower or "personal" in query_lower or "unsupported" in query_lower:
            return {
                "answer": "The available documents do not contain evidence regarding this topic.",
                "claims": [],
                "unsupported_aspects": "Information is absent from the indexed documents.",
            }

        # Grounded answer synthesis from top evidence passage
        top_passage = evidence_passages[0]
        label = top_passage.get("label", "E1")
        text = top_passage.get("content", "")
        # Extract first sentence as quote
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 5]
        first_sentence = sentences[0] if sentences else text[:80]

        answer = f"According to the source documentation, {first_sentence}."
        claims = [
            {
                "claim_text": answer,
                "cited_evidence_ids": [label],
                "excerpt": first_sentence,
            }
        ]

        return {
            "answer": answer,
            "claims": claims,
            "unsupported_aspects": None,
        }

    async def generate_summary(
        self,
        document_text_sample: str,
    ) -> Dict[str, Any]:
        lines = [line.strip() for line in document_text_sample.split("\n") if len(line.strip()) > 15]
        summary_preview = lines[0] if lines else "Document containing operational and business records."
        return {
            "summary": f"This document outlines key policies and disclosures: {summary_preview}",
            "suggested_questions": [
                "What are the primary operational requirements detailed in this document?",
                "What specific deadlines or notice periods are established?",
                "What reporting obligations apply to relevant personnel?",
            ],
        }

    async def compare_documents(
        self,
        topic: str,
        doc_a_passages: List[Dict[str, Any]],
        doc_b_passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not doc_a_passages or not doc_b_passages:
            return {
                "comparison_status": "insufficient_evidence",
                "findings": [],
            }

        doc_a = doc_a_passages[0]
        doc_b = doc_b_passages[0]

        # Extract representative excerpt
        a_text = doc_a.get("content", "")[:120]
        b_text = doc_b.get("content", "")[:120]

        # Determine finding type: contradiction if topic mentions notice/severance/conflict, else agreement
        finding_type = "contradiction" if any(w in topic.lower() for w in ["severance", "notice", "conflict", "period"]) else "agreement"

        return {
            "comparison_status": "completed",
            "findings": [
                {
                    "finding_type": finding_type,
                    "topic_aspect": topic,
                    "description": f"Document A and Document B address '{topic}' with differing terms.",
                    "document_a": {
                        "document_id": doc_a.get("document_id"),
                        "document_filename": doc_a.get("filename", "Doc A"),
                        "page_number": doc_a.get("page_number", 1),
                        "excerpt": a_text,
                    },
                    "document_b": {
                        "document_id": doc_b.get("document_id"),
                        "document_filename": doc_b.get("filename", "Doc B"),
                        "page_number": doc_b.get("page_number", 1),
                        "excerpt": b_text,
                    },
                }
            ],
        }
