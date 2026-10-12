"""Google Gemini API embedding adapter using gemini-embedding-2 (FR-04, FR-05)."""

import asyncio
import random
from typing import List
import httpx
from app.adapters.base import EmbeddingAdapter
from app.core.config import settings
from app.core.errors import ProviderUnavailableException, QuotaExhaustedException
from app.core.logging import logger


class GeminiEmbeddingAdapter(EmbeddingAdapter):
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self):
        self.api_key = settings.EMBEDDING_API_KEY.get_secret_value()
        self.model = settings.EMBEDDING_MODEL.replace("models/", "")
        self.dim = settings.EMBEDDING_DIMENSIONS

    async def _post_with_retry(self, endpoint: str, json_data: dict, max_retries: int = 3) -> dict:
        url = f"{self.BASE_URL}/{endpoint}?key={self.api_key}"
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(url, json=json_data)

                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 429:
                    if attempt == max_retries - 1:
                        raise QuotaExhaustedException("Gemini API rate limit or quota exceeded.")
                    backoff = (2 ** attempt) + random.uniform(0.1, 0.5)
                    await asyncio.sleep(backoff)
                elif resp.status_code >= 500:
                    if attempt == max_retries - 1:
                        raise ProviderUnavailableException("Gemini API server unavailable.")
                    await asyncio.sleep(1.0)
                else:
                    err_msg = resp.text[:200]
                    raise ProviderUnavailableException(f"Gemini API returned error HTTP {resp.status_code}: {err_msg}")
            except (httpx.TimeoutException, httpx.NetworkError):
                if attempt == max_retries - 1:
                    raise ProviderUnavailableException("Gemini API connection timeout.")
                await asyncio.sleep(1.0)

    async def embed_query(self, query: str) -> List[float]:
        endpoint = f"models/{self.model}:embedContent"
        payload = {
            "model": f"models/{self.model}",
            "content": {"parts": [{"text": query}]},
            "outputDimensionality": self.dim,
        }
        res = await self._post_with_retry(endpoint, payload)
        return res.get("embedding", {}).get("values", [])

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # Batch embed up to settings.EMBEDDING_BATCH_SIZE
        embeddings: List[List[float]] = []
        for i in range(0, len(texts), settings.EMBEDDING_BATCH_SIZE):
            batch = texts[i : i + settings.EMBEDDING_BATCH_SIZE]
            endpoint = f"models/{self.model}:batchEmbedContents"
            requests = [
                {
                    "model": f"models/{self.model}",
                    "content": {"parts": [{"text": t}]},
                    "outputDimensionality": self.dim,
                }
                for t in batch
            ]
            res = await self._post_with_retry(endpoint, {"requests": requests})
            batch_vals = [e.get("values", []) for e in res.get("embeddings", [])]
            embeddings.extend(batch_vals)
        return embeddings
