"""LLM service for generating responses using Ollama."""

import logging

import httpx

from config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """Generates text responses using Ollama LLM."""

    def __init__(self, model: str | None = None) -> None:
        settings = get_settings()
        self.model = model or settings.ollama_llm_model
        self.base_url = settings.ollama_base_url

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate a response from the LLM."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=300.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]

    async def chat(
        self,
        messages: list[dict],
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> str:
        """Generate a chat response from a list of messages."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature,
                    },
                },
                timeout=300.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
