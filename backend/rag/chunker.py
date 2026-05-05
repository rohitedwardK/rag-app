"""Text chunking utilities for RAG processing."""

from typing import List


class TextChunker:
    """Splits text into overlapping chunks for embedding."""

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks."""
        if not text or not text.strip():
            return []

        text = text.strip()

        if len(text) <= self.chunk_size:
            return [text]

        chunks: List[str] = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size

            if end < len(text):
                break_point = text.rfind(" ", start, end)
                if break_point > start:
                    end = break_point

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            start = end - self.chunk_overlap
            if start >= len(text):
                break

        return chunks
