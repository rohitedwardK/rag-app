"""Embedding service using Ollama."""

import logging
from typing import List

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Generates embeddings using Ollama's embedding models."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self.model = model or settings.ollama_embed_model
        self.base_url = settings.ollama_base_url

    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["embedding"]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings: List[List[float]] = []
        for text in texts:
            embedding = await self.embed_text(text)
            embeddings.append(embedding)
        return embeddings
