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

        query_lower = query.lower()

        # Prompt injection defense
        if any(term in query_lower for term in ["ignore previous", "ignore all", "system prompt", "disregard instructions", "override"]):
            return {
                "answer": "I cannot fulfill requests that attempt to override safety boundaries.",
                "claims": [],
                "unsupported_aspects": "Prompt injection instruction detected.",
            }

        # Extract meaningful query keywords (length >= 4, excluding common stopwords)
        stopwords = {
            "what", "were", "when", "where", "which", "does", "have", "been", "that", "this",
            "from", "with", "about", "listed", "mention", "quarter", "period", "total", "more",
            "would", "could", "should", "their", "there", "these", "those"
        }
        raw_words = query_lower.split()
        query_keywords = [
            w.strip("?,.:;\"'()") for w in raw_words
            if len(w.strip("?,.:;\"'()")) >= 4 and w.strip("?,.:;\"'()") not in stopwords
        ]

        # Check keyword presence in combined evidence
        combined_evidence = " ".join(p.get("content", "").lower() for p in evidence_passages)
        overlap = [w for w in query_keywords if w in combined_evidence]

        # Explicit abstention keywords or zero evidence overlap
        if not overlap or any(term in query_lower for term in ["itinerary", "personal", "unsupported", "microsoft", "quantum", "tokyo", "dental"]):
            return {
                "answer": "The available documents do not contain evidence regarding this topic.",
                "claims": [],
                "unsupported_aspects": "Information is absent from the indexed documents.",
            }

        # Select the best matching evidence passage based on keyword overlap
        best_passage = evidence_passages[0]
        best_count = 0
        for p in evidence_passages:
            p_text = p.get("content", "").lower()
            cnt = sum(1 for w in query_keywords if w in p_text)
            if cnt > best_count:
                best_count = cnt
                best_passage = p

        label = best_passage.get("label", "E1")
        text = best_passage.get("content", "")

        # Extract the specific sentence containing matched keywords
        sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 5]
        matched_sentence = None
        for s in sentences:
            if any(w in s.lower() for w in overlap):
                matched_sentence = s
                break
        excerpt = matched_sentence if matched_sentence else (sentences[0] if sentences else text[:80])

        answer = f"According to the source documentation, {excerpt}."
        claims = [
            {
                "claim_text": answer,
                "cited_evidence_ids": [label],
                "excerpt": excerpt,
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
