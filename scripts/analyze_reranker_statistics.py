"""Deterministic paired statistics from an existing reranker result artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import random
from statistics import mean
from typing import Any, Callable


def _hit(rank: int | None, cutoff: int) -> float:
    return float(rank is not None and rank <= cutoff)


def _reciprocal_rank(rank: int | None, cutoff: int) -> float:
    return 1.0 / rank if rank is not None and rank <= cutoff else 0.0


def _percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * probability
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def paired_bootstrap(
    query_results: list[dict[str, Any]],
    *,
    treatment: str,
    control: str,
    score: Callable[[int | None], float],
    resamples: int = 5000,
    seed: int = 20260808,
) -> dict[str, float | int]:
    if resamples < 1000:
        raise ValueError("resamples must be at least 1000")
    deltas = [
        score(query["methods"][treatment]["first_relevant_rank"])
        - score(query["methods"][control]["first_relevant_rank"])
        for query in query_results
    ]
    if not deltas:
        raise ValueError("query_results must not be empty")
    generator = random.Random(seed)
    bootstrap_deltas = [
        mean(generator.choice(deltas) for _ in deltas)
        for _ in range(resamples)
    ]
    return {
        "queries": len(deltas),
        "observed_delta": mean(deltas),
        "ci95_low": _percentile(bootstrap_deltas, 0.025),
        "ci95_high": _percentile(bootstrap_deltas, 0.975),
        "resamples": resamples,
        "seed": seed,
    }


def error_taxonomy(
    query_results: list[dict[str, Any]],
    *,
    control: str,
    treatment: str,
    evidence_k: int,
) -> dict[str, int]:
    counts = {
        "hit_to_hit": 0,
        "miss_to_hit": 0,
        "hit_to_miss": 0,
        "miss_to_miss": 0,
        "candidate_positive_but_treatment_outside_top5": 0,
        "retrieval_miss": 0,
    }
    for query in query_results:
        positive = query["positive_passage_sha256"]
        if positive not in query["candidate_ids"]:
            counts["retrieval_miss"] += 1
        before = query["methods"][control]["first_relevant_rank"]
        after = query["methods"][treatment]["first_relevant_rank"]
        before_hit = before is not None and before <= evidence_k
        after_hit = after is not None and after <= evidence_k
        counts[f"{'hit' if before_hit else 'miss'}_to_{'hit' if after_hit else 'miss'}"] += 1
        if positive in query["candidate_ids"] and not after_hit:
            counts["candidate_positive_but_treatment_outside_top5"] += 1
    return counts


def analyze(result: dict[str, Any], *, resamples: int, seed: int) -> dict[str, Any]:
    queries = result["query_results"]
    evidence_k = int(result["evidence_k"])
    metrics = {
        "hit@1": lambda rank: _hit(rank, 1),
        "hit@5": lambda rank: _hit(rank, evidence_k),
        "mrr@5": lambda rank: _reciprocal_rank(rank, evidence_k),
    }
    comparisons = {}
    for control in ("no_rerank", "base_cross_encoder"):
        comparisons[f"fine_tuned_cross_encoder_minus_{control}"] = {
            metric: paired_bootstrap(
                queries,
                treatment="fine_tuned_cross_encoder",
                control=control,
                score=score,
                resamples=resamples,
                seed=seed,
            )
            for metric, score in metrics.items()
        }
    return {
        "schema_version": 1,
        "source_schema_version": result.get("schema_version"),
        "candidate_source": result["candidate_source"],
        "corpus_passages": result["corpus_passages"],
        "queries": len(queries),
        "evidence_k": evidence_k,
        "comparisons": comparisons,
        "error_taxonomy_base_to_fine_tuned": error_taxonomy(
            queries,
            control="base_cross_encoder",
            treatment="fine_tuned_cross_encoder",
            evidence_k=evidence_k,
        ),
        "claim_boundary": (
            "Paired uncertainty over the locked query set on the same corpus; "
            "not document-generalization, RAGAS, generation, or production evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("artifacts/benchmark/reranker_comparison.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmark/reranker_statistics.json"),
    )
    parser.add_argument("--resamples", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260808)
    args = parser.parse_args()
    result = json.loads(args.input.read_text(encoding="utf-8"))
    analysis = analyze(result, resamples=args.resamples, seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(analysis, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(analysis, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
