"""Reciprocal Rank Fusion for dense and lexical candidate lists."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass(frozen=True)
class FusedCandidate:
    candidate: RankedCandidate
    rrf_score: float
    rank: int
    source_ranks: Dict[str, int]


def reciprocal_rank_fusion(
    rankings: Mapping[str, Iterable[RankedCandidate]],
    *,
    top_k: int = 20,
    rank_constant: int = 60,
) -> List[FusedCandidate]:
    """Fuse independent rankings without comparing their raw score scales."""
    if top_k <= 0:
        return []
    if rank_constant < 0:
        raise ValueError("rank_constant must be non-negative")

    candidates: Dict[str, RankedCandidate] = {}
    scores: Dict[str, float] = {}
    source_ranks: Dict[str, Dict[str, int]] = {}

    for source, ranking in rankings.items():
        seen_in_source: set[str] = set()
        for rank, candidate in enumerate(ranking, start=1):
            if candidate.candidate_id in seen_in_source:
                continue
            seen_in_source.add(candidate.candidate_id)
            candidates.setdefault(candidate.candidate_id, candidate)
            scores[candidate.candidate_id] = scores.get(candidate.candidate_id, 0.0) + (
                1.0 / (rank_constant + rank)
            )
            source_ranks.setdefault(candidate.candidate_id, {})[source] = rank

    ordered_ids = sorted(scores, key=lambda candidate_id: (-scores[candidate_id], candidate_id))
    return [
        FusedCandidate(
            candidate=candidates[candidate_id],
            rrf_score=scores[candidate_id],
            rank=rank,
            source_ranks=source_ranks[candidate_id],
        )
        for rank, candidate_id in enumerate(ordered_ids[:top_k], start=1)
    ]
