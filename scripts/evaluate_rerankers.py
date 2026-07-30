"""Compare locked reranking methods over the same hybrid top-20 candidates."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter
from typing import Any

import numpy as np
from sentence_transformers import CrossEncoder


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_dataset import locate_default_arrow, read_arrow_rows
from scripts.run_bm25_baseline import build_unique_passage_corpus, passage_id, percentile
from scripts.run_dense_hybrid_baseline import (
    _candidate_from_bm25,
    _candidate_from_dense,
    load_or_encode_corpus,
)
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DensePassageIndex
from src.hybrid_retriever import RankedCandidate, reciprocal_rank_fusion
from src.local_embedding import LocalE5EmbeddingModel
from src.mmr_reranker import maximal_marginal_relevance
from src.retrieval_metrics import aggregate_query_metrics, evaluate_query_ranking


METHODS = ("no_rerank", "mmr", "base_cross_encoder", "fine_tuned_cross_encoder")


def _cross_encoder_ranking(
    model: CrossEncoder,
    question: str,
    candidates: list[RankedCandidate],
) -> list[RankedCandidate]:
    scores = np.asarray(
        model.predict(
            [[question, candidate.content] for candidate in candidates],
            show_progress_bar=False,
            convert_to_numpy=True,
        )
    ).reshape(-1)
    return [
        candidate
        for _, candidate in sorted(
            zip(scores.tolist(), candidates),
            key=lambda item: (-float(item[0]), item[1].candidate_id),
        )
    ]


def _summary(metrics, latencies_ms: list[float]) -> dict[str, float]:
    output = aggregate_query_metrics(metrics)
    output.update(
        {
            "latency_p50_ms": median(latencies_ms) if latencies_ms else 0.0,
            "latency_p95_ms": percentile(latencies_ms, 0.95),
        }
    )
    return output


def evaluate_rerankers(
    rows: list[dict[str, Any]],
    split_manifest: dict[str, Any],
    embedding_model: LocalE5EmbeddingModel,
    base_model: CrossEncoder,
    fine_tuned_model: CrossEncoder,
    *,
    embedding_cache: Path | None,
    candidate_k: int = 20,
    evidence_k: int = 5,
    batch_size: int = 32,
    mmr_relevance_weight: float = 0.7,
) -> dict[str, Any]:
    documents = build_unique_passage_corpus(rows)
    passage_embeddings, cache_hit, corpus_sha256 = load_or_encode_corpus(
        embedding_model,
        documents,
        cache_path=embedding_cache,
        batch_size=batch_size,
    )
    dense_index = DensePassageIndex(documents, passage_embeddings)
    bm25 = BM25Retriever(documents)
    embeddings_by_id = {
        document.document_id: passage_embeddings[index]
        for index, document in enumerate(documents)
    }

    metrics_by_method = {method: [] for method in METHODS}
    latencies_by_method = {method: [] for method in METHODS}
    query_results: list[dict[str, Any]] = []

    for entry in split_manifest["splits"]["test"]:
        row_index = int(entry["row_index"])
        row = rows[row_index]
        question = str(row.get("question") or "")
        contexts = [str(context) for context in (row.get("context") or [])]
        positive_id = passage_id(contexts[0])

        query_embedding = embedding_model.encode_queries([question], batch_size=1)[0]
        dense_results = dense_index.retrieve(query_embedding, top_k=candidate_k)
        bm25_results = bm25.retrieve(question, top_k=candidate_k)
        fused = reciprocal_rank_fusion(
            {
                "dense": [_candidate_from_dense(item) for item in dense_results],
                "bm25": [_candidate_from_bm25(item) for item in bm25_results],
            },
            top_k=candidate_k,
        )
        candidates = [item.candidate for item in fused]

        rankings: dict[str, list[RankedCandidate]] = {"no_rerank": candidates}
        timings: dict[str, float] = {"no_rerank": 0.0}

        started = perf_counter()
        rankings["mmr"] = maximal_marginal_relevance(
            candidates,
            query_embedding,
            embeddings_by_id,
            top_k=candidate_k,
            relevance_weight=mmr_relevance_weight,
        )
        timings["mmr"] = (perf_counter() - started) * 1000.0

        started = perf_counter()
        rankings["base_cross_encoder"] = _cross_encoder_ranking(
            base_model, question, candidates
        )
        timings["base_cross_encoder"] = (perf_counter() - started) * 1000.0

        started = perf_counter()
        rankings["fine_tuned_cross_encoder"] = _cross_encoder_ranking(
            fine_tuned_model, question, candidates
        )
        timings["fine_tuned_cross_encoder"] = (perf_counter() - started) * 1000.0

        query_output = {
            "row_index": row_index,
            "question_sha256": entry["question_sha256"],
            "positive_passage_sha256": positive_id,
            "candidate_ids": [candidate.candidate_id for candidate in candidates],
            "methods": {},
        }
        for method in METHODS:
            ranked_ids = [candidate.candidate_id for candidate in rankings[method]]
            metrics = evaluate_query_ranking(ranked_ids, {positive_id})
            metrics_by_method[method].append(metrics)
            latencies_by_method[method].append(timings[method])
            query_output["methods"][method] = {
                "first_relevant_rank": metrics.first_relevant_rank,
                "evidence_ids": ranked_ids[:evidence_k],
                "rerank_latency_ms": timings[method],
            }
        query_results.append(query_output)

    summaries = {
        method: _summary(metrics_by_method[method], latencies_by_method[method])
        for method in METHODS
    }
    return {
        "schema_version": 1,
        "candidate_source": "dense_top20_plus_bm25_top20_rrf_k60",
        "candidate_k": candidate_k,
        "evidence_k": evidence_k,
        "mmr_relevance_weight": mmr_relevance_weight,
        "embedding_model": embedding_model.model_name,
        "corpus_passages": len(documents),
        "corpus_sha256": corpus_sha256,
        "embedding_cache_hit": cache_hit,
        "split_source_sha256": split_manifest["source_sha256"],
        "label_contract": split_manifest["label_contract"],
        "summaries": summaries,
        "query_results": query_results,
        "claim_boundary": (
            "Locked-test passage reranking only; candidate and MMR settings were "
            "frozen before test. This is not RAGAS or generation evaluation."
        ),
    }


def build_error_analysis(result: dict[str, Any]) -> dict[str, Any]:
    transitions: dict[str, int] = {}
    examples_by_transition: dict[str, list[dict[str, Any]]] = {}
    residual_misses: list[dict[str, Any]] = []
    for query in result["query_results"]:
        before = query["methods"]["base_cross_encoder"]["first_relevant_rank"]
        after = query["methods"]["fine_tuned_cross_encoder"]["first_relevant_rank"]
        before_bucket = "miss" if before is None or before > result["evidence_k"] else "hit"
        after_bucket = "miss" if after is None or after > result["evidence_k"] else "hit"
        key = f"{before_bucket}_to_{after_bucket}"
        transitions[key] = transitions.get(key, 0) + 1
        if before != after:
            examples_by_transition.setdefault(key, []).append(
                {
                    "row_index": query["row_index"],
                    "question_sha256": query["question_sha256"],
                    "base_rank": before,
                    "fine_tuned_rank": after,
                }
            )
        if after_bucket == "miss":
            residual_misses.append(
                {
                    "row_index": query["row_index"],
                    "question_sha256": query["question_sha256"],
                    "fine_tuned_rank": after,
                    "candidate_contains_positive": after is not None,
                }
            )
    for examples in examples_by_transition.values():
        examples.sort(
            key=lambda item: (
                item["fine_tuned_rank"] if item["fine_tuned_rank"] is not None else 999,
                item["row_index"],
            )
        )
    residual_misses.sort(key=lambda item: item["row_index"])
    return {
        "schema_version": 1,
        "evidence_k": result["evidence_k"],
        "transitions": transitions,
        "changed_rank_examples_by_transition": {
            key: values[:10] for key, values in sorted(examples_by_transition.items())
        },
        "residual_fine_tuned_misses": residual_misses,
        "interpretation_rule": (
            "Inspect hit-to-miss regressions and miss-to-hit gains; hashes preserve "
            "test integrity without copying private source text."
        ),
    }


def write_comparison_csv(result: dict[str, Any], path: Path) -> None:
    fields = [
        "method",
        "queries",
        "recall@20",
        "hit@1",
        "hit@3",
        "hit@5",
        "mrr",
        "ndcg@10",
        "latency_p50_ms",
        "latency_p95_ms",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for method in METHODS:
            summary = result["summaries"][method]
            writer.writerow({"method": method, **{key: summary.get(key, "") for key in fields[1:]}})


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate locked reranking methods")
    parser.add_argument("--arrow", type=Path)
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("artifacts/data/split_manifest.json"),
    )
    parser.add_argument(
        "--fine-tuned-checkpoint",
        type=Path,
        default=Path("checkpoints/reranker/full/best"),
    )
    parser.add_argument(
        "--embedding-cache",
        type=Path,
        default=Path(".cache/retrieval/multilingual_e5_small_passages.npz"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmark/reranker_comparison.json"),
    )
    parser.add_argument(
        "--comparison-csv",
        type=Path,
        default=Path("artifacts/benchmark/reranker_comparison.csv"),
    )
    parser.add_argument(
        "--error-analysis",
        type=Path,
        default=Path("artifacts/benchmark/reranker_error_analysis.json"),
    )
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}))
        return 2
    if not args.split_manifest.is_file() or not args.fine_tuned_checkpoint.is_dir():
        print(json.dumps({"error": "split manifest or fine-tuned checkpoint missing"}))
        return 2

    split_manifest = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    embedding_model = LocalE5EmbeddingModel(device=args.device)
    base_model = CrossEncoder(
        "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1",
        device=args.device,
        max_length=256,
    )
    fine_tuned_model = CrossEncoder(
        str(args.fine_tuned_checkpoint),
        device=args.device,
        max_length=256,
    )
    result = evaluate_rerankers(
        read_arrow_rows(arrow_path),
        split_manifest,
        embedding_model,
        base_model,
        fine_tuned_model,
        embedding_cache=args.embedding_cache,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_comparison_csv(result, args.comparison_csv)
    args.error_analysis.write_text(
        json.dumps(build_error_analysis(result), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result["summaries"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
