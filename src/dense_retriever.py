"""Cosine/dot-product retrieval over normalized local passage embeddings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import numpy as np

from src.bm25_retriever import LexicalDocument


@dataclass(frozen=True)
class DenseResult:
    document: LexicalDocument
    score: float
    rank: int


class DensePassageIndex:
    def __init__(
        self,
        documents: Sequence[LexicalDocument],
        embeddings,
    ):
        matrix = np.asarray(embeddings, dtype=np.float32)
        if matrix.ndim != 2:
            raise ValueError("embeddings must be a 2D matrix")
        if len(documents) != matrix.shape[0]:
            raise ValueError("document and embedding counts must match")
        self.documents = list(documents)
        self.embeddings = matrix

    def retrieve(self, query_embedding, *, top_k: int = 20) -> List[DenseResult]:
        if top_k <= 0 or not self.documents:
            return []
        query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
        if query.shape[0] != self.embeddings.shape[1]:
            raise ValueError("query embedding dimension does not match index")

        scores = self.embeddings @ query
        order = sorted(
            range(len(self.documents)),
            key=lambda index: (-float(scores[index]), self.documents[index].document_id),
        )[:top_k]
        return [
            DenseResult(
                document=self.documents[index],
                score=float(scores[index]),
                rank=rank,
            )
            for rank, index in enumerate(order, start=1)
        ]
