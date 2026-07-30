"""Run local multilingual E5 Dense and Dense+BM25 RRF baselines."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from statistics import median
import sys
from time import perf_counter
from typing import Any

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_dataset import locate_default_arrow, read_arrow_rows
from scripts.run_bm25_baseline import build_unique_passage_corpus, passage_id, percentile
from src.bm25_retriever import BM25Retriever
from src.dense_retriever import DensePassageIndex
from src.hybrid_retriever import RankedCandidate, reciprocal_rank_fusion
from src.local_embedding import LocalE5EmbeddingModel
from src.retrieval_metrics import aggregate_query_metrics, evaluate_query_ranking


def corpus_hash(document_ids: list[str]) -> str:
    return hashlib.sha256("\n".join(document_ids).encode("utf-8")).hexdigest()


def load_or_encode_corpus(
    model: LocalE5EmbeddingModel,
    documents,
    *,
    cache_path: Path | None,
    batch_size: int,
):
    document_ids = [document.document_id for document in documents]
    expected_hash = corpus_hash(document_ids)

    if cache_path and cache_path.is_file():
        cached = np.load(cache_path, allow_pickle=False)
        cached_model = str(cached["model_name"].item())
        cached_hash = str(cached["corpus_hash"].item())
        embeddings = cached["embeddings"]
        if cached_model == model.model_name and cached_hash == expected_hash:
            return embeddings, True, expected_hash

    embeddings = model.encode_passages(
        [document.content for document in documents],
        batch_size=batch_size,
    )
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            cache_path,
            embeddings=np.asarray(embeddings, dtype=np.float32),
            model_name=np.asarray(model.model_name),
            corpus_hash=np.asarray(expected_hash),
        )
    return embeddings, False, expected_hash


def _candidate_from_dense(result) -> RankedCandidate:
    return RankedCandidate(
        candidate_id=result.document.document_id,
        content=result.document.content,
        metadata=result.document.metadata,
        score=result.score,
    )


def _candidate_from_bm25(result) -> RankedCandidate:
    return RankedCandidate(
        candidate_id=result.document.document_id,
        content=result.document.content,
        metadata=result.document.metadata,
        score=result.score,
    )


def _summary(metrics, latencies_ms: list[float]) -> dict[str, float]:
    output = aggregate_query_metrics(metrics)
    output.update(
        {
            "latency_p50_ms": median(latencies_ms) if latencies_ms else 0.0,
            "latency_p95_ms": percentile(latencies_ms, 0.95),
        }
    )
    return output


def run_dense_hybrid_baseline(
    rows: list[dict[str, Any]],
    split_manifest: dict[str, Any],
    model: LocalE5EmbeddingModel,
    *,
    cache_path: Path | None,
    top_k: int = 20,
    batch_size: int = 32,
) -> dict[str, Any]:
    documents = build_unique_passage_corpus(rows)
    passage_embeddings, cache_hit, corpus_sha256 = load_or_encode_corpus(
        model,
        documents,
        cache_path=cache_path,
        batch_size=batch_size,
    )
    dense_index = DensePassageIndex(documents, passage_embeddings)
    bm25 = BM25Retriever(documents)

    metrics_by_method = {"dense": [], "bm25": [], "hybrid_rrf": []}
    latencies_by_method = {"dense": [], "bm25": [], "hybrid_rrf": []}
    query_results = []

    for entry in split_manifest["splits"]["test"]:
        row_index = int(entry["row_index"])
        row = rows[row_index]
        question = str(row.get("question") or "")
        contexts = [str(context) for context in (row.get("context") or [])]
        positive_id = passage_id(contexts[0])

        dense_started = perf_counter()
        query_embedding = model.encode_queries([question], batch_size=1)[0]
        dense_results = dense_index.retrieve(query_embedding, top_k=top_k)
        dense_latency = (perf_counter() - dense_started) * 1000.0

        bm25_started = perf_counter()
        bm25_results = bm25.retrieve(question, top_k=top_k)
        bm25_latency = (perf_counter() - bm25_started) * 1000.0

        fusion_started = perf_counter()
        fused_results = reciprocal_rank_fusion(
            {
                "dense": [_candidate_from_dense(result) for result in dense_results],
                "bm25": [_candidate_from_bm25(result) for result in bm25_results],
            },
            top_k=top_k,
        )
        fusion_latency = (perf_counter() - fusion_started) * 1000.0

        ranking_ids = {
            "dense": [result.document.document_id for result in dense_results],
            "bm25": [result.document.document_id for result in bm25_results],
            "hybrid_rrf": [result.candidate.candidate_id for result in fused_results],
        }
        latencies = {
            "dense": dense_latency,
            "bm25": bm25_latency,
            "hybrid_rrf": dense_latency + bm25_latency + fusion_latency,
        }
        query_output = {
            "row_index": row_index,
            "question_sha256": entry["question_sha256"],
            "positive_passage_sha256": positive_id,
            "methods": {},
        }
        for method, ranked_ids in ranking_ids.items():
            metrics = evaluate_query_ranking(ranked_ids, {positive_id})
            metrics_by_method[method].append(metrics)
            latencies_by_method[method].append(latencies[method])
            query_output["methods"][method] = {
                "first_relevant_rank": metrics.first_relevant_rank,
                "latency_ms": latencies[method],
                "top_candidate_ids": ranked_ids,
            }
        query_results.append(query_output)

    summaries = {
        method: _summary(metrics_by_method[method], latencies_by_method[method])
        for method in metrics_by_method
    }
    return {
        "schema_version": 1,
        "model_name": model.model_name,
        "top_k": top_k,
        "corpus_passages": len(documents),
        "corpus_sha256": corpus_sha256,
        "embedding_cache_hit": cache_hit,
        "split_source_sha256": split_manifest["source_sha256"],
        "label_contract": split_manifest["label_contract"],
        "summaries": summaries,
        "query_results": query_results,
        "claim_boundary": "Locked-test passage retrieval; not RAGAS or generation evaluation.",
    }


def write_comparison_csv(result: dict[str, Any], output: Path) -> None:
    fields = [
        "method",
        "queries",
        "corpus_passages",
        "recall@20",
        "hit@1",
        "hit@3",
        "hit@5",
        "mrr",
        "ndcg@10",
        "latency_p50_ms",
        "latency_p95_ms",
    ]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for method in ("dense", "bm25", "hybrid_rrf"):
            summary = result["summaries"][method]
            writer.writerow(
                {
                    "method": method,
                    "queries": int(summary["queries"]),
                    "corpus_passages": result["corpus_passages"],
                    **{
                        field: summary.get(field, "")
                        for field in fields
                        if field not in {"method", "queries", "corpus_passages"}
                    },
                }
            )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Dense and Hybrid locked baselines")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("artifacts/data/split_manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmark/dense_hybrid_baseline.json"),
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=Path("artifacts/benchmark/retrieval_comparison.csv"),
    )
    parser.add_argument(
        "--cache",
        type=Path,
        default=Path(".cache/retrieval/multilingual_e5_small_passages.npz"),
    )
    parser.add_argument("--model", default="intfloat/multilingual-e5-small")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--top-k", type=int, default=20)
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}, indent=2))
        return 2
    if not args.split_manifest.is_file():
        print(json.dumps({"error": "locked split manifest not found"}, indent=2))
        return 2

    split_manifest = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    model = LocalE5EmbeddingModel(args.model, device=args.device)
    result = run_dense_hybrid_baseline(
        read_arrow_rows(arrow_path),
        split_manifest,
        model,
        cache_path=args.cache,
        top_k=args.top_k,
        batch_size=args.batch_size,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_comparison_csv(result, args.comparison_output)
    print(json.dumps(result["summaries"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
