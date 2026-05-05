"""Prompt templates for RAG-based responses."""

SYSTEM_PROMPT = """You are a helpful document assistant.

Answer questions based ONLY on the provided document context.

Rules:
- If the answer is not in the context, say: "I could not find this information in the uploaded documents."
- Do not make up information
- Be concise and clear
- Cite the source document when helpful"""


RAG_PROMPT_TEMPLATE = """Context from uploaded documents:
{context}

---

User Question: {question}

Answer based only on the context above."""


def build_rag_prompt(context_chunks: list[str], question: str) -> str:
    """Build a RAG prompt with context and question."""
    context = "\n\n".join(context_chunks)
    return RAG_PROMPT_TEMPLATE.format(context=context, question=question)


def build_messages(context_chunks: list[str], question: str) -> list[dict]:
    """Build message list for chat-style LLM API."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_rag_prompt(context_chunks, question)},
    ]
