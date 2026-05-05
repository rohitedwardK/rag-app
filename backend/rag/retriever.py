"""Retriever for fetching relevant context from vector store."""

import logging

from rag.embeddings import EmbeddingService
from rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class Retriever:
    """Retrieves relevant document chunks for a query using vector similarity search."""

    def __init__(self) -> None:
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()

    async def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> list[dict]:
        """Retrieve relevant chunks for a query."""
        query_embedding = await self.embedding_service.embed_text(query)

        results = self.vector_store.query(
            query_embedding=query_embedding,
            n_results=top_k,
        )

        chunks = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, doc in enumerate(documents):
            chunks.append({
                "text": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "distance": distances[i] if i < len(distances) else None,
            })

        return chunks

    async def retrieve_with_sources(
        self,
        query: str,
        top_k: int = 5,
    ) -> tuple[list[str], list[str]]:
        """Retrieve relevant chunks and their source filenames."""
        chunks = await self.retrieve(query, top_k)

        texts = [chunk["text"] for chunk in chunks]
        sources = []
        seen_files = set()

        for chunk in chunks:
            filename = chunk.get("metadata", {}).get("filename")
            if filename and filename not in seen_files:
                sources.append(filename)
                seen_files.add(filename)

        return texts, sources
