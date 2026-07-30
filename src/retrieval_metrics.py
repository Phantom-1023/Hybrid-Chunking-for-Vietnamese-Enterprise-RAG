"""Passage-aware retrieval metrics for locked candidate rankings."""

from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import mean
from typing import Dict, Iterable, List, Sequence, Set


@dataclass(frozen=True)
class QueryRetrievalMetrics:
    first_relevant_rank: int | None
    recall_at: Dict[int, float]
    hit_at: Dict[int, float]
    reciprocal_rank: float
    ndcg_at: Dict[int, float]


def _dcg(relevances: Sequence[int], k: int) -> float:
    return sum(
        relevance / math.log2(rank + 1)
        for rank, relevance in enumerate(relevances[:k], start=1)
    )


def evaluate_query_ranking(
    ranked_ids: Sequence[str],
    relevant_ids: Set[str],
    *,
    cutoffs: Iterable[int] = (1, 3, 5, 20),
    ndcg_cutoffs: Iterable[int] = (5, 10, 20),
) -> QueryRetrievalMetrics:
    if not relevant_ids:
        raise ValueError("relevant_ids must not be empty")

    first_rank = next(
        (rank for rank, candidate_id in enumerate(ranked_ids, start=1) if candidate_id in relevant_ids),
        None,
    )
    recalls: Dict[int, float] = {}
    hits: Dict[int, float] = {}
    for cutoff in cutoffs:
        retrieved_relevant = len(set(ranked_ids[:cutoff]) & relevant_ids)
        recalls[cutoff] = retrieved_relevant / len(relevant_ids)
        hits[cutoff] = 1.0 if retrieved_relevant else 0.0

    relevances = [1 if candidate_id in relevant_ids else 0 for candidate_id in ranked_ids]
    ideal = [1] * min(len(relevant_ids), len(ranked_ids))
    ndcg: Dict[int, float] = {}
    for cutoff in ndcg_cutoffs:
        ideal_dcg = _dcg(ideal, cutoff)
        ndcg[cutoff] = _dcg(relevances, cutoff) / ideal_dcg if ideal_dcg else 0.0

    return QueryRetrievalMetrics(
        first_relevant_rank=first_rank,
        recall_at=recalls,
        hit_at=hits,
        reciprocal_rank=1.0 / first_rank if first_rank else 0.0,
        ndcg_at=ndcg,
    )


def aggregate_query_metrics(
    metrics: Sequence[QueryRetrievalMetrics],
) -> Dict[str, float]:
    if not metrics:
        return {}

    output: Dict[str, float] = {
        "queries": float(len(metrics)),
        "mrr": mean(item.reciprocal_rank for item in metrics),
    }
    recall_cutoffs = sorted({cutoff for item in metrics for cutoff in item.recall_at})
    hit_cutoffs = sorted({cutoff for item in metrics for cutoff in item.hit_at})
    ndcg_cutoffs = sorted({cutoff for item in metrics for cutoff in item.ndcg_at})

    for cutoff in recall_cutoffs:
        output[f"recall@{cutoff}"] = mean(item.recall_at[cutoff] for item in metrics)
    for cutoff in hit_cutoffs:
        output[f"hit@{cutoff}"] = mean(item.hit_at[cutoff] for item in metrics)
    for cutoff in ndcg_cutoffs:
        output[f"ndcg@{cutoff}"] = mean(item.ndcg_at[cutoff] for item in metrics)
    return output
