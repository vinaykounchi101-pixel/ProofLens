"""Abstract base interfaces for Embedding and LLM Provider adapters."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class EmbeddingAdapter(ABC):
    @abstractmethod
    async def embed_query(self, query: str) -> List[float]:
        """Embeds a single search query string into a vector."""
        pass

    @abstractmethod
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embeds a batch of document chunk strings into vectors."""
        pass


class LLMAdapter(ABC):
    @abstractmethod
    async def generate_grounded_answer(
        self,
        query: str,
        evidence_passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generates an answer grounded strictly in supplied evidence passages.
        Returns a structured dictionary with:
        - answer: str
        - claims: List[Dict[str, Any]] with cited_evidence_ids
        - unsupported_aspects: Optional[str]
        """
        pass

    @abstractmethod
    async def generate_summary(
        self,
        document_text_sample: str,
    ) -> Dict[str, Any]:
        """
        Generates a concise document summary and 3 suggested questions.
        Returns:
        - summary: str
        - suggested_questions: List[str]
        """
        pass

    @abstractmethod
    async def compare_documents(
        self,
        topic: str,
        doc_a_passages: List[Dict[str, Any]],
        doc_b_passages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generates structured cross-document findings on a topic.
        """
        pass
