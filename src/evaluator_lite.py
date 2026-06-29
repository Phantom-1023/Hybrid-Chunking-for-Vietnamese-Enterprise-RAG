"""
Small real evaluation-lite benchmark for the current MVP.

This intentionally does not claim to be RAGAS. It measures retrieval hits,
retrieval distance, and a simple answer/ground-truth keyword overlap.
"""

from dataclasses import dataclass
import csv
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set

from config.constants import VERIFY_STRATEGIES
from config.settings import settings
from src.dataset_loader import DatasetLoadError, RagDatasetRecord, load_vietnamese_rag_snapshot
from src.retriever import RetrievedChunk, StrategyRetriever


class EvaluationLiteError(RuntimeError):
    """Raised when evaluation-lite cannot complete."""


@dataclass
class StrategyEvaluationResult:
    """One CSV row for a chunking strategy."""

    strategy: str
    evaluation_type: str
    sample_count: int
    top1_hit_rate: float
    topk_hit_rate: float
    avg_distance: float
    answer_keyword_overlap: float
    avg_score: float
    note: str


def run_evaluation_lite(
    limit: int = 5,
    top_k: int = 5,
    output_path: str = "benchmark_results.csv",
) -> List[StrategyEvaluationResult]:
    """Evaluate 4 strategy collections on a tiny real dataset slice."""
    sample_limit = max(1, min(int(limit or 5), 5))
    top_k = max(1, int(top_k or 5))

    try:
        snapshot = load_vietnamese_rag_snapshot(
            dataset_name=settings.verify_dataset_name,
            config_name=settings.verify_dataset_config,
            limit=sample_limit,
        )
    except DatasetLoadError:
        raise
    except Exception as exc:
        raise EvaluationLiteError(f"Could not load evaluation dataset: {exc}") from exc

    records = [
        record for record in snapshot.selected_records
        if record.question and record.ground_truth
    ][:sample_limit]
    if not records:
        raise EvaluationLiteError("No evaluation records with both question and ground_truth.")

    retriever = StrategyRetriever()
    results: List[StrategyEvaluationResult] = []
    generation_note = (
        "LLM generation enabled."
        if settings.eval_use_llm_generation
        else "LLM generation skipped for safety; overlap uses retrieved source chunks."
    )

    for strategy in VERIFY_STRATEGIES:
        top1_hits = 0
        topk_hits = 0
        distances: List[float] = []
        overlaps: List[float] = []

        for record in records:
            chunks = retriever.retrieve(
                question=record.question or "",
                strategy=strategy,
                top_k=top_k,
            )
            if not chunks:
                continue

            distances.extend(chunk.distance for chunk in chunks)
            expected_record_id = str(record.record_id)
            if _same_record(chunks[0], expected_record_id):
                top1_hits += 1
            if any(_same_record(chunk, expected_record_id) for chunk in chunks):
                topk_hits += 1

            answer = _build_evaluation_answer(record.question or "", chunks)
            overlaps.append(_keyword_overlap(answer, record.ground_truth or ""))

        sample_count = len(records)
        avg_distance = _mean(distances)
        top1_hit_rate = top1_hits / sample_count
        topk_hit_rate = topk_hits / sample_count
        answer_keyword_overlap = _mean(overlaps)
        distance_score = 1.0 / (1.0 + max(avg_distance, 0.0))
        avg_score = _mean([
            top1_hit_rate,
            topk_hit_rate,
            distance_score,
            answer_keyword_overlap,
        ])

        results.append(
            StrategyEvaluationResult(
                strategy=strategy,
                evaluation_type="evaluation-lite",
                sample_count=sample_count,
                top1_hit_rate=top1_hit_rate,
                topk_hit_rate=topk_hit_rate,
                avg_distance=avg_distance,
                answer_keyword_overlap=answer_keyword_overlap,
                avg_score=avg_score,
                note=f"This is evaluation-lite, not full RAGAS. {generation_note}",
            )
        )

    _write_csv(Path(output_path), results)
    return results


def _same_record(chunk: RetrievedChunk, expected_record_id: str) -> bool:
    return str(chunk.metadata.get("record_id", "")) == expected_record_id


def _keyword_overlap(answer: str, ground_truth: str) -> float:
    expected_keywords = _keywords(ground_truth)
    if not expected_keywords:
        return 0.0
    answer_keywords = _keywords(answer)
    return len(expected_keywords & answer_keywords) / len(expected_keywords)


def _build_evaluation_answer(question: str, chunks: List[RetrievedChunk]) -> str:
    if settings.eval_use_llm_generation:
        from src.generator import AnswerGenerator

        return AnswerGenerator().generate(question, chunks)
    return "\n\n".join(chunk.content for chunk in chunks)


def _keywords(text: str) -> Set[str]:
    tokens = re.findall(r"[\wÀ-ỹ]+", (text or "").lower(), flags=re.UNICODE)
    return {
        token for token in tokens
        if len(token) >= 3 and token not in _VIETNAMESE_STOPWORDS
    }


def _mean(values: Iterable[float]) -> float:
    values = list(values)
    return sum(values) / len(values) if values else 0.0


def _write_csv(path: Path, results: List[StrategyEvaluationResult]) -> None:
    fieldnames = [
        "strategy",
        "evaluation_type",
        "sample_count",
        "top1_hit_rate",
        "topk_hit_rate",
        "avg_distance",
        "answer_keyword_overlap",
        "avg_score",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow({
                "strategy": result.strategy,
                "evaluation_type": result.evaluation_type,
                "sample_count": result.sample_count,
                "top1_hit_rate": f"{result.top1_hit_rate:.4f}",
                "topk_hit_rate": f"{result.topk_hit_rate:.4f}",
                "avg_distance": f"{result.avg_distance:.4f}",
                "answer_keyword_overlap": f"{result.answer_keyword_overlap:.4f}",
                "avg_score": f"{result.avg_score:.4f}",
                "note": result.note,
            })


_VIETNAMESE_STOPWORDS = {
    "của", "cho", "các", "một", "những", "được", "trong", "ngoài", "trên",
    "dưới", "với", "vào", "này", "kia", "đó", "là", "và", "hoặc", "khi",
    "thì", "đã", "đang", "sẽ", "không", "chưa", "the", "and", "for", "that",
}
