from app.adapters.base import EmbeddingAdapter, LLMAdapter
from app.adapters.mock_adapter import MockEmbeddingAdapter, MockLLMAdapter
from app.adapters.gemini_embedding import GeminiEmbeddingAdapter
from app.adapters.gemini_llm import GeminiLLMAdapter
from app.core.config import settings


def get_embedding_adapter() -> EmbeddingAdapter:
    if settings.EMBEDDING_PROVIDER.lower() == "gemini" and settings.EMBEDDING_API_KEY.get_secret_value():
        return GeminiEmbeddingAdapter()
    return MockEmbeddingAdapter(dim=settings.EMBEDDING_DIMENSIONS)


def get_llm_adapter() -> LLMAdapter:
    if settings.LLM_PROVIDER.lower() == "gemini" and settings.LLM_API_KEY.get_secret_value():
        return GeminiLLMAdapter()
    return MockLLMAdapter()


__all__ = [
    "EmbeddingAdapter",
    "LLMAdapter",
    "MockEmbeddingAdapter",
    "MockLLMAdapter",
    "GeminiEmbeddingAdapter",
    "GeminiLLMAdapter",
    "get_embedding_adapter",
    "get_llm_adapter",
]
