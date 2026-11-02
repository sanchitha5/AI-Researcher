"""
Google Gemini embedding model.

Uses Google's Gemini embeddings API via LangChain's Google Generative AI integration.
Requires GEMINI_API_KEY in backend/.env.
"""

from functools import lru_cache

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings


class GeminiNotConfiguredError(Exception):
    """Raised when an embedding operation is attempted without GEMINI_API_KEY."""


@lru_cache(maxsize=1)
def get_embedding_model() -> GoogleGenerativeAIEmbeddings:
    """Return a cached instance of the Google Gemini embedding model."""
    if not settings.GEMINI_API_KEY:
        raise GeminiNotConfiguredError(
            "GEMINI_API_KEY is not configured. Please set GEMINI_API_KEY in backend/.env"
        )
    return GoogleGenerativeAIEmbeddings(
        model=settings.GEMINI_EMBEDDING_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
    )

