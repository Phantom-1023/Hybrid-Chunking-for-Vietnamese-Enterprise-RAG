"""
Minimal Gemini API helpers for Milestone 1 verification.
"""

from dataclasses import dataclass
from typing import List

from config.settings import settings


class MissingGeminiApiKey(RuntimeError):
    """Raised when GEMINI_API_KEY is not configured."""


class GeminiEmbeddingError(RuntimeError):
    """Raised when the Gemini embedding call fails."""


class GeminiGenerationError(RuntimeError):
    """Raised when the Gemini generation call fails."""


@dataclass
class GeminiEmbeddingResult:
    """Embedding result returned by Gemini."""

    model: str
    vector: List[float]

    @property
    def dimension(self) -> int:
        return len(self.vector)


class GeminiService:
    """Tiny Gemini client wrapper for verifying text-embedding-004."""

    def __init__(self, api_key: str = "", embedding_model: str = ""):
        self.api_key = api_key or settings.gemini_api_key
        self.embedding_model = embedding_model or settings.gemini_embedding_model

    def embed_text(self, text: str) -> GeminiEmbeddingResult:
        return self.embed_texts([text])[0]

    def embed_texts(self, texts: List[str]) -> List[GeminiEmbeddingResult]:
        if not self.api_key:
            raise MissingGeminiApiKey("Missing GEMINI_API_KEY. Please set it in .env")

        try:
            from google import genai
        except ImportError as exc:
            raise GeminiEmbeddingError(
                "Missing google-genai package. Please install dependencies from requirements.txt."
            ) from exc

        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.embed_content(
                model=self.embedding_model,
                contents=texts,
            )
        except Exception as exc:
            raise GeminiEmbeddingError(f"Gemini embedding request failed: {exc}") from exc

        vectors = _extract_embedding_vectors(response)
        if not vectors:
            raise GeminiEmbeddingError("Gemini embedding response did not contain vectors.")
        if len(vectors) != len(texts):
            raise GeminiEmbeddingError(
                f"Gemini embedding response count mismatch: expected {len(texts)}, got {len(vectors)}."
            )

        return [
            GeminiEmbeddingResult(model=self.embedding_model, vector=vector)
            for vector in vectors
        ]

    def generate_text(self, prompt: str, model: str = "") -> str:
        if not self.api_key:
            raise MissingGeminiApiKey("Missing GEMINI_API_KEY. Please set it in .env")

        try:
            from google import genai
        except ImportError as exc:
            raise GeminiGenerationError(
                "Missing google-genai package. Please install dependencies from requirements.txt."
            ) from exc

        generation_model = model or settings.gemini_flash_model
        try:
            client = genai.Client(api_key=self.api_key)
            response = client.models.generate_content(
                model=generation_model,
                contents=prompt,
            )
        except Exception as exc:
            raise GeminiGenerationError(f"Gemini generation request failed: {exc}") from exc

        text = getattr(response, "text", "") or ""
        if not text.strip():
            raise GeminiGenerationError("Gemini generation response did not contain text.")
        return text.strip()


def _extract_embedding_vector(response) -> List[float]:
    vectors = _extract_embedding_vectors(response)
    return vectors[0] if vectors else []


def _extract_embedding_vectors(response) -> List[List[float]]:
    embeddings = getattr(response, "embeddings", None)
    if embeddings:
        vectors = []
        for embedding in embeddings:
            values = getattr(embedding, "values", None)
            if values:
                vectors.append(list(values))
        return vectors

    embedding = getattr(response, "embedding", None)
    if embedding:
        values = getattr(embedding, "values", None)
        if values:
            return [list(values)]

    if isinstance(response, dict):
        if response.get("embeddings"):
            return [
                list(item.get("values", []))
                for item in response["embeddings"]
                if item.get("values")
            ]
        if response.get("embedding"):
            values = response["embedding"].get("values", [])
            return [list(values)] if values else []

    return []
