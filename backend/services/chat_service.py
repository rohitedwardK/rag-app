"""Chat service for RAG-based responses."""

import logging

from rag.retriever import Retriever
from rag.llm import LLMService
from rag.prompts import build_messages

logger = logging.getLogger(__name__)


class ChatService:
    """Handles chat interactions with RAG."""

    def __init__(self) -> None:
        self.retriever = Retriever()
        self.llm = LLMService()

    async def chat(
        self,
        message: str,
        top_k: int = 5,
    ) -> dict:
        """
        Process a chat message using RAG.
        
        Returns the response with sources.
        """
        context_chunks, sources = await self.retriever.retrieve_with_sources(
            query=message,
            top_k=top_k,
        )

        if not context_chunks:
            return {
                "response": "I don't have any documents to search. Please upload some documents first.",
                "sources": [],
            }

        messages = build_messages(context_chunks, message)

        response = await self.llm.chat(messages)

        return {
            "response": response,
            "sources": sources,
        }
