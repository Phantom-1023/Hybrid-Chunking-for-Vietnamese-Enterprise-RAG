"""Run a locked-test BM25 passage baseline on Vietnamese_RAG."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_dataset import locate_default_arrow, normalize_text, read_arrow_rows
from src.bm25_retriever import BM25Retriever, LexicalDocument
from src.retrieval_metrics import aggregate_query_metrics, evaluate_query_ranking


def passage_id(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def build_unique_passage_corpus(rows: list[dict[str, Any]]) -> list[LexicalDocument]:
    documents: dict[str, LexicalDocument] = {}
    for row_index, row in enumerate(rows):
        raw_contexts = row.get("context") or []
        contexts = (
            [str(raw_contexts)]
            if isinstance(raw_contexts, str)
            else [str(context) for context in raw_contexts]
        )
        for passage_index, context in enumerate(contexts):
            candidate_id = passage_id(context)
            documents.setdefault(
                candidate_id,
                LexicalDocument(
                    document_id=candidate_id,
                    content=context,
                    metadata={
                        "first_row_index": row_index,
                        "first_passage_index": passage_index,
                    },
                ),
            )
    return sorted(documents.values(), key=lambda document: document.document_id)


def percentile(values: list[float], probability: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math_ceil(probability * len(ordered)) - 1))
    return ordered[index]


def math_ceil(value: float) -> int:
    integer = int(value)
    return integer if value == integer else integer + 1


def run_bm25_baseline(
    rows: list[dict[str, Any]],
    split_manifest: dict[str, Any],
    *,
    top_k: int = 20,
) -> dict[str, Any]:
    corpus = build_unique_passage_corpus(rows)
    retriever = BM25Retriever(corpus)
    test_entries = split_manifest["splits"]["test"]
    query_metrics = []
    query_results = []
    latencies_ms: list[float] = []

    for entry in test_entries:
        row_index = int(entry["row_index"])
        row = rows[row_index]
        contexts = [str(context) for context in (row.get("context") or [])]
        if not contexts:
            raise ValueError(f"row {row_index} has no contexts")

        started = perf_counter()
        results = retriever.retrieve(str(row.get("question") or ""), top_k=top_k)
        latency_ms = (perf_counter() - started) * 1000.0
        latencies_ms.append(latency_ms)

        ranked_ids = [result.document.document_id for result in results]
        positive_id = passage_id(contexts[0])
        metrics = evaluate_query_ranking(ranked_ids, {positive_id})
        query_metrics.append(metrics)
        query_results.append(
            {
                "row_index": row_index,
                "question_sha256": entry["question_sha256"],
                "positive_passage_sha256": positive_id,
                "first_relevant_rank": metrics.first_relevant_rank,
                "latency_ms": latency_ms,
                "top_candidate_ids": ranked_ids,
            }
        )

    summary = aggregate_query_metrics(query_metrics)
    summary.update(
        {
            "latency_p50_ms": median(latencies_ms) if latencies_ms else 0.0,
            "latency_p95_ms": percentile(latencies_ms, 0.95),
        }
    )
    return {
        "schema_version": 1,
        "method": "bm25",
        "top_k": top_k,
        "corpus_passages": len(corpus),
        "split_source_sha256": split_manifest["source_sha256"],
        "label_contract": split_manifest["label_contract"],
        "summary": summary,
        "query_results": query_results,
        "claim_boundary": "Locked-test passage retrieval baseline; not RAGAS.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run locked-test BM25 baseline")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("artifacts/data/split_manifest.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/benchmark/bm25_baseline.json"),
    )
    parser.add_argument(
        "--comparison-output",
        type=Path,
        default=Path("artifacts/benchmark/retrieval_comparison.csv"),
    )
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
    result = run_bm25_baseline(
        read_arrow_rows(arrow_path),
        split_manifest,
        top_k=args.top_k,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    args.comparison_output.parent.mkdir(parents=True, exist_ok=True)
    comparison_fields = [
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
    comparison_row = {
        "method": result["method"],
        "queries": int(result["summary"]["queries"]),
        "corpus_passages": result["corpus_passages"],
        **{
            field: result["summary"].get(field, "")
            for field in comparison_fields
            if field not in {"method", "queries", "corpus_passages"}
        },
    }
    with args.comparison_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=comparison_fields)
        writer.writeheader()
        writer.writerow(comparison_row)
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
