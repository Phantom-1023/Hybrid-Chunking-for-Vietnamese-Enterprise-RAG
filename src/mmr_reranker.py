"""Maximal Marginal Relevance baseline over dense candidate embeddings."""

from __future__ import annotations

from typing import Mapping, Sequence

import numpy as np

from src.hybrid_retriever import RankedCandidate


def maximal_marginal_relevance(
    candidates: Sequence[RankedCandidate],
    query_embedding,
    candidate_embeddings: Mapping[str, np.ndarray],
    *,
    top_k: int = 20,
    relevance_weight: float = 0.7,
) -> list[RankedCandidate]:
    if not 0.0 <= relevance_weight <= 1.0:
        raise ValueError("relevance_weight must be between 0 and 1")
    if top_k <= 0:
        return []

    query = np.asarray(query_embedding, dtype=np.float32).reshape(-1)
    remaining = list(candidates)
    selected: list[RankedCandidate] = []

    while remaining and len(selected) < top_k:
        best = None
        best_score = float("-inf")
        for candidate in remaining:
            embedding = np.asarray(
                candidate_embeddings[candidate.candidate_id],
                dtype=np.float32,
            ).reshape(-1)
            relevance = float(embedding @ query)
            redundancy = max(
                (
                    float(
                        embedding
                        @ np.asarray(
                            candidate_embeddings[item.candidate_id],
                            dtype=np.float32,
                        ).reshape(-1)
                    )
                    for item in selected
                ),
                default=0.0,
            )
            score = relevance_weight * relevance - (
                1.0 - relevance_weight
            ) * redundancy
            if (
                score > best_score
                or (
                    score == best_score
                    and best is not None
                    and candidate.candidate_id < best.candidate_id
                )
            ):
                best = candidate
                best_score = score

        selected.append(best)
        remaining = [
            candidate
            for candidate in remaining
            if candidate.candidate_id != best.candidate_id
        ]

    return selected
