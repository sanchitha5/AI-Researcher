"""
Application configuration.

Everything the app needs from the environment is loaded here, once,
so the rest of the codebase can simply do:

    from app.config import settings
    settings.GROQ_API_KEY

This is the ONLY place that should read `os.environ` / `.env` directly.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Absolute path to the backend/ directory (parent of app/)
BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
CHROMA_DIR = DATA_DIR / "chroma"
DOCUMENTS_METADATA_FILE = DATA_DIR / "documents.json"


class Settings(BaseSettings):
    # --- Groq (LLM) ---
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "openai/gpt-oss-120b"

    # --- Tavily (web search) ---
    TAVILY_API_KEY: str = ""

    # --- LangSmith (optional) ---
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "ai-research-agent"

    # --- Gemini (Embeddings) ---
    GEMINI_API_KEY: str = ""
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # --- Uploads ---
    MAX_UPLOAD_MB: int = 25

    # --- Agent behaviour ---
    MAX_RETRIES: int = 2

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_MB * 1024 * 1024

    @property
    def groq_configured(self) -> bool:
        return bool(self.GROQ_API_KEY)

    @property
    def tavily_configured(self) -> bool:
        return bool(self.TAVILY_API_KEY)

    @property
    def gemini_configured(self) -> bool:
        return bool(self.GEMINI_API_KEY)


settings = Settings()

# Make sure the data directories exist before anything tries to write to them.
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)

# Wire up LangSmith tracing ONLY if the user actually enabled it.
# If left disabled (the default), the app works normally with zero
# LangSmith dependency.
if settings.LANGCHAIN_TRACING_V2 and settings.LANGCHAIN_API_KEY:
    import os

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = settings.LANGCHAIN_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = settings.LANGCHAIN_PROJECT
