"""
Minimal AI provider gateway for mission indexing.
"""

from typing import List

from config.settings import settings
from src.gemini_service import GeminiEmbeddingError, GeminiService, MissingGeminiApiKey


class EmbeddingProviderError(RuntimeError):
    """Raised when the configured embedding provider cannot embed text."""


class EmbeddingProvider:
    """Provider gateway. Currently supports Gemini embeddings only."""

    def __init__(self, provider_name: str = ""):
        self.provider_name = (provider_name or settings.embedding_provider).lower()
        if self.provider_name != "gemini":
            raise EmbeddingProviderError(
                f"Unsupported EMBEDDING_PROVIDER='{self.provider_name}'. Current mission supports only 'gemini'."
            )
        if not settings.gemini_api_key:
            raise MissingGeminiApiKey("Missing GEMINI_API_KEY. Please set it in .env")
        self._gemini = GeminiService()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        try:
            results = self._gemini.embed_texts(texts)
        except MissingGeminiApiKey:
            raise
        except GeminiEmbeddingError as exc:
            raise EmbeddingProviderError(str(exc)) from exc

        return [result.vector for result in results]

    def embed_text(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]
