"""Read-only integrity audit for the cached Vietnamese_RAG Arrow snapshot.

The script prints aggregate statistics only. It never prints questions,
answers, contexts, API keys, or other record contents.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip().casefold())


def content_hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def duplicate_stats(values: Iterable[str]) -> dict[str, int]:
    hashes = [content_hash(value) for value in values if normalize_text(value)]
    counts = Counter(hashes)
    return {
        "non_empty": len(hashes),
        "unique": len(counts),
        "duplicate_groups": sum(1 for count in counts.values() if count > 1),
        "duplicate_rows_beyond_first": sum(count - 1 for count in counts.values() if count > 1),
        "largest_group": max(counts.values(), default=0),
    }


def shared_context_group_stats(context_rows: list[list[str]]) -> dict[str, int]:
    """Build record groups connected by at least one identical context passage."""
    parent = list(range(len(context_rows)))

    def find(item: int) -> int:
        while parent[item] != item:
            parent[item] = parent[parent[item]]
            item = parent[item]
        return item

    def union(left: int, right: int) -> None:
        left_root = find(left)
        right_root = find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    first_record_by_passage: dict[str, int] = {}
    for row_index, contexts in enumerate(context_rows):
        for passage in contexts:
            if not normalize_text(passage):
                continue
            passage_digest = content_hash(passage)
            first = first_record_by_passage.setdefault(passage_digest, row_index)
            union(first, row_index)

    sizes = Counter(find(index) for index in range(len(context_rows)))
    return {
        "groups": len(sizes),
        "multi_record_groups": sum(1 for size in sizes.values() if size > 1),
        "rows_in_multi_record_groups": sum(size for size in sizes.values() if size > 1),
        "largest_group_rows": max(sizes.values(), default=0),
    }


def locate_default_arrow() -> Path | None:
    root = Path.home() / ".cache" / "huggingface" / "datasets"
    matches = sorted(root.glob("sailor2___vietnamese_rag/BKAI_RAG/**/*.arrow"))
    return matches[-1] if matches else None


def read_arrow_rows(path: Path) -> list[dict[str, Any]]:
    try:
        import pyarrow as pa
    except ImportError as exc:
        raise RuntimeError(
            "Missing pyarrow. Install the approved data-audit dependency first."
        ) from exc

    with pa.memory_map(str(path), "r") as source:
        try:
            table = pa.ipc.open_stream(source).read_all()
        except pa.ArrowInvalid:
            source.seek(0)
            table = pa.ipc.open_file(source).read_all()
    return table.to_pylist()


def audit_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required = ("question", "answer", "context")
    missing_fields = Counter()
    empty_fields = Counter()
    questions: list[str] = []
    answers: list[str] = []
    context_documents: list[str] = []
    context_passages: list[str] = []
    context_rows: list[list[str]] = []
    context_lengths: list[int] = []

    for row in rows:
        for field in required:
            if field not in row:
                missing_fields[field] += 1

        question = row.get("question") or ""
        answer = row.get("answer") or ""
        contexts = row.get("context") or []
        if isinstance(contexts, str):
            contexts = [contexts]

        if not normalize_text(str(question)):
            empty_fields["question"] += 1
        if not normalize_text(str(answer)):
            empty_fields["answer"] += 1
        if not contexts or not any(normalize_text(str(item)) for item in contexts):
            empty_fields["context"] += 1

        questions.append(str(question))
        answers.append(str(answer))
        normalized_contexts = [str(item) for item in contexts]
        context_rows.append(normalized_contexts)
        context_passages.extend(normalized_contexts)
        context_documents.append("\n".join(normalized_contexts))
        context_lengths.append(len(normalized_contexts))

    return {
        "rows": len(rows),
        "required_fields": list(required),
        "missing_field_rows": dict(missing_fields),
        "empty_field_rows": dict(empty_fields),
        "contexts_per_row": {
            "min": min(context_lengths, default=0),
            "max": max(context_lengths, default=0),
            "total_passages": sum(context_lengths),
        },
        "exact_duplicate_audit": {
            "question": duplicate_stats(questions),
            "answer": duplicate_stats(answers),
            "joined_context_per_row": duplicate_stats(context_documents),
            "individual_context_passage": duplicate_stats(context_passages),
        },
        "record_groups_by_shared_context": shared_context_group_stats(context_rows),
        "split_guardrail": (
            "Group duplicate normalized questions and contexts before splitting; "
            "never create train/dev/test by chunk after chunking."
        ),
        "privacy": "Aggregate counts and SHA-256 comparisons only; record text is not printed.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit cached Vietnamese_RAG data")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}, indent=2))
        return 2

    result = audit_rows(read_arrow_rows(arrow_path))
    result["source"] = {
        "filename": arrow_path.name,
        "size_bytes": arrow_path.stat().st_size,
        "sha256": hashlib.sha256(arrow_path.read_bytes()).hexdigest(),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
