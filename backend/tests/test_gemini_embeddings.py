import pytest
from unittest.mock import patch
from app.rag.embeddings import get_embedding_model, GeminiNotConfiguredError
from app.config import settings

def test_gemini_embedding_raises_when_not_configured():
    get_embedding_model.cache_clear()
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with pytest.raises(GeminiNotConfiguredError):
            get_embedding_model()
    get_embedding_model.cache_clear()

def test_gemini_embedding_instantiates_with_key():
    get_embedding_model.cache_clear()
    with patch.object(settings, "GEMINI_API_KEY", "test-key"):
        with patch("app.rag.embeddings.GoogleGenerativeAIEmbeddings") as mock_cls:
            model = get_embedding_model()
            mock_cls.assert_called_once_with(
                model=settings.GEMINI_EMBEDDING_MODEL,
                google_api_key="test-key",
            )
    get_embedding_model.cache_clear()
