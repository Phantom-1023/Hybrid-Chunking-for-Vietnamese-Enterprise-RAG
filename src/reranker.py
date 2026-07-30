"""Fine-tuned Cross-Encoder reranker used by the live query pipeline."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path
from typing import Any, Sequence

import numpy as np


class RerankerError(RuntimeError):
    """Raised when the approved checkpoint cannot be verified or loaded."""


def checkpoint_tree_sha256(path: Path) -> str:
    if not path.is_dir():
        raise RerankerError(f"Checkpoint directory does not exist: {path}")
    digest = hashlib.sha256()
    files = sorted(item for item in path.rglob("*") if item.is_file())
    if not files:
        raise RerankerError(f"Checkpoint directory is empty: {path}")
    for file_path in files:
        digest.update(file_path.relative_to(path).as_posix().encode("utf-8"))
        digest.update(b"\0")
        with file_path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class RerankedItem:
    item: Any
    score: float


class CrossEncoderReranker:
    """Load a checksum-verified checkpoint and score query/passage pairs."""

    def __init__(
        self,
        checkpoint_path: str | Path,
        *,
        expected_sha256: str = "",
        device: str | None = None,
        model=None,
    ):
        self.checkpoint_path = Path(checkpoint_path)
        self.checkpoint_sha256 = (
            checkpoint_tree_sha256(self.checkpoint_path)
            if model is None or expected_sha256
            else ""
        )
        if expected_sha256 and self.checkpoint_sha256 != expected_sha256:
            raise RerankerError(
                "Reranker checkpoint checksum mismatch; refusing to serve it."
            )
        if model is not None:
            self.model = model
            return
        try:
            from sentence_transformers import CrossEncoder

            self.model = CrossEncoder(str(self.checkpoint_path), device=device)
        except Exception as exc:
            raise RerankerError(
                f"Could not load reranker checkpoint '{self.checkpoint_path}': {exc}"
            ) from exc

    def rerank(
        self,
        question: str,
        items: Sequence[Any],
        *,
        top_k: int = 5,
    ) -> list[RerankedItem]:
        if top_k <= 0 or not items:
            return []
        pairs = [[question, str(item.content)] for item in items]
        scores = np.asarray(
            self.model.predict(
                pairs,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
        ).reshape(-1)
        if len(scores) != len(items):
            raise RerankerError("Reranker returned an unexpected number of scores.")
        ranked = sorted(
            zip(scores.tolist(), items),
            key=lambda pair: (-float(pair[0]), str(pair[1].content)),
        )
        return [
            RerankedItem(item=item, score=float(score))
            for score, item in ranked[:top_k]
        ]
