"""Audit whether Vietnamese_RAG contexts can support reliable positive labels.

The default output is aggregate-only. It does not print questions, answers, or
passages. Exact answer containment is evidence, not a universal semantic label:
rows without an exact match remain unresolved for a later annotation contract.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any

from audit_dataset import locate_default_arrow, normalize_text, read_arrow_rows


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"\w+", normalize_text(value), flags=re.UNICODE))


def answer_token_recall(answer: str, passage: str) -> float:
    answer_tokens = _tokens(answer)
    if not answer_tokens:
        return 0.0
    return len(answer_tokens & _tokens(passage)) / len(answer_tokens)


def exact_match_positions(answer: str, contexts: list[str]) -> list[int]:
    normalized_answer = normalize_text(answer)
    if not normalized_answer:
        return []
    return [
        index
        for index, context in enumerate(contexts)
        if normalized_answer in normalize_text(context)
    ]


def audit_positive_labels(rows: list[dict[str, Any]]) -> dict[str, Any]:
    exact_position_counts: Counter[int] = Counter()
    best_overlap_position_counts: Counter[int] = Counter()
    exact_context_zero = 0
    exact_only_context_zero = 0
    exact_only_later_context = 0
    exact_multiple_contexts = 0
    unresolved = 0

    for row in rows:
        answer = str(row.get("answer") or "")
        raw_contexts = row.get("context") or []
        contexts = (
            [str(raw_contexts)]
            if isinstance(raw_contexts, str)
            else [str(context) for context in raw_contexts]
        )

        exact_positions = exact_match_positions(answer, contexts)
        for position in exact_positions:
            exact_position_counts[position] += 1

        if 0 in exact_positions:
            exact_context_zero += 1
        if exact_positions == [0]:
            exact_only_context_zero += 1
        elif exact_positions and 0 not in exact_positions:
            exact_only_later_context += 1
        elif len(exact_positions) > 1:
            exact_multiple_contexts += 1
        elif not exact_positions:
            unresolved += 1

        recalls = [answer_token_recall(answer, context) for context in contexts]
        if recalls:
            best_overlap_position_counts[max(range(len(recalls)), key=recalls.__getitem__)] += 1

    total = len(rows)
    exact_anywhere = total - unresolved
    return {
        "rows": total,
        "method": {
            "exact": "normalized full-answer substring containment",
            "fallback_signal": "answer-token recall; diagnostic only, not a label",
        },
        "exact_match": {
            "any_context_rows": exact_anywhere,
            "any_context_rate": exact_anywhere / total if total else 0.0,
            "context_zero_rows": exact_context_zero,
            "context_zero_rate": exact_context_zero / total if total else 0.0,
            "only_context_zero_rows": exact_only_context_zero,
            "only_later_context_rows": exact_only_later_context,
            "multiple_context_rows": exact_multiple_contexts,
            "unresolved_rows": unresolved,
            "position_counts": dict(sorted(exact_position_counts.items())),
        },
        "best_answer_token_recall_position_counts": dict(
            sorted(best_overlap_position_counts.items())
        ),
        "label_contract": (
            "Exact matches identify defensible positive passages. Rows without an "
            "exact match remain unresolved and must not be silently labeled context[0]."
        ),
        "privacy": "Aggregate counts only; no record text is printed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit positive-passage label evidence")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    parser.add_argument("--output", type=Path, help="Optional aggregate JSON artifact")
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}, indent=2))
        return 2

    result = audit_positive_labels(read_arrow_rows(arrow_path))
    rendered = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
