"""Fail-closed local multilingual E5 embedding wrapper."""

from __future__ import annotations

from typing import Iterable


class LocalEmbeddingError(RuntimeError):
    """Raised when the approved local embedding model cannot run."""


class LocalE5EmbeddingModel:
    def __init__(
        self,
        model_name: str = "intfloat/multilingual-e5-small",
        *,
        device: str | None = None,
        model=None,
    ):
        self.model_name = model_name
        if model is not None:
            self.model = model
            return

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise LocalEmbeddingError(
                "sentence-transformers is required for the local E5 baseline"
            ) from exc

        try:
            self.model = SentenceTransformer(model_name, device=device)
        except Exception as exc:
            raise LocalEmbeddingError(
                f"Could not load approved embedding model '{model_name}': {exc}"
            ) from exc

    def encode_passages(self, passages: Iterable[str], *, batch_size: int = 32):
        return self._encode(
            [f"passage: {passage}" for passage in passages],
            batch_size=batch_size,
        )

    def encode_queries(self, queries: Iterable[str], *, batch_size: int = 32):
        return self._encode(
            [f"query: {query}" for query in queries],
            batch_size=batch_size,
        )

    def _encode(self, values: list[str], *, batch_size: int):
        try:
            return self.model.encode(
                values,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=True,
                show_progress_bar=False,
            )
        except Exception as exc:
            raise LocalEmbeddingError(
                f"Embedding failed for '{self.model_name}': {exc}"
            ) from exc
