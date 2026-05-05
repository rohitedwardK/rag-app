"""Vector store interface for ChromaDB (embedded mode)."""

import logging
from typing import List, Dict, Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings

logger = logging.getLogger(__name__)

_client: chromadb.ClientAPI | None = None


def get_chroma_client() -> chromadb.ClientAPI:
    """Get or create the ChromaDB client (persistent, embedded mode)."""
    global _client
    if _client is None:
        settings = get_settings()
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


class VectorStore:
    """Interface for storing and querying vectors in ChromaDB."""

    COLLECTION_NAME = "documents"

    def __init__(self) -> None:
        """Initialize the ChromaDB client."""
        self.client = get_chroma_client()

    def get_collection(self) -> chromadb.Collection:
        """Get or create the documents collection."""
        return self.client.get_or_create_collection(
            name=self.COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(
        self,
        chunk_ids: List[str],
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Add chunks with their embeddings to the vector store."""
        collection = self.get_collection()
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
    ) -> Dict[str, Any]:
        """Query the vector store for similar chunks."""
        collection = self.get_collection()
        return collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            include=["documents", "metadatas", "distances"],
        )

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all documents in the collection."""
        collection = self.get_collection()
        result = collection.get(include=["metadatas"])
        
        docs = []
        seen_files = set()
        for meta in result.get("metadatas", []):
            filename = meta.get("filename")
            if filename and filename not in seen_files:
                seen_files.add(filename)
                docs.append({
                    "filename": filename,
                    "uploaded_at": meta.get("uploaded_at", ""),
                })
        return docs

    def delete_by_filename(self, filename: str) -> None:
        """Delete all chunks for a specific file."""
        collection = self.get_collection()
        collection.delete(where={"filename": filename})

    def clear_all(self) -> None:
        """Delete all documents from the collection."""
        try:
            self.client.delete_collection(self.COLLECTION_NAME)
        except Exception:
            pass
