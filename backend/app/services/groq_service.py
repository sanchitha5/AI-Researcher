"""
Groq LLM service.

Wraps LangChain's ChatGroq client so the rest of the app can just
call `get_llm().invoke(...)` without worrying about API keys or
model configuration — those live in app/config.py, driven by the
GROQ_API_KEY and GROQ_MODEL environment variables.
"""

from functools import lru_cache

from langchain_groq import ChatGroq

from app.config import settings


class GroqNotConfiguredError(Exception):
    """Raised when a Groq call is attempted without an API key set."""


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.2) -> ChatGroq:
    if not settings.groq_configured:
        raise GroqNotConfiguredError(
            "GROQ_API_KEY is not set. Add it to backend/.env to enable the AI agent."
        )
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=settings.GROQ_MODEL,
        temperature=temperature,
    )
