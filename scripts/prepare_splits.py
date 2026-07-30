"""Create a deterministic query-generalization split manifest.

The manifest stores IDs and hashes only. It fails closed on duplicate questions
because the current approved protocol requires each query to belong to one split.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
from typing import Any

from audit_dataset import locate_default_arrow, normalize_text, read_arrow_rows


DEFAULT_RATIOS = {"train": 0.8, "dev": 0.1, "test": 0.1}
DEFAULT_SEED = 42
APPROVED_LABEL_CONTRACTS = {
    "context-zero-verified",
    "multiple-positive-annotated",
}


def text_hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def allocate_counts(total: int, ratios: dict[str, float]) -> dict[str, int]:
    if total < 0 or not ratios:
        raise ValueError("total and ratios must be valid")
    if abs(sum(ratios.values()) - 1.0) > 1e-9:
        raise ValueError("ratios must sum to 1.0")

    raw = {name: total * ratio for name, ratio in ratios.items()}
    counts = {name: int(value) for name, value in raw.items()}
    remainder = total - sum(counts.values())
    order = sorted(ratios, key=lambda name: (-(raw[name] - counts[name]), name))
    for name in order[:remainder]:
        counts[name] += 1
    return counts


def build_split_manifest(
    rows: list[dict[str, Any]],
    *,
    source_sha256: str,
    label_contract: str,
    seed: int = DEFAULT_SEED,
    ratios: dict[str, float] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if label_contract not in APPROVED_LABEL_CONTRACTS:
        raise ValueError("label contract has not passed its audit gate")

    ratios = ratios or DEFAULT_RATIOS
    indexed: list[dict[str, Any]] = []
    question_hash_counts: Counter[str] = Counter()

    for index, row in enumerate(rows):
        question = str(row.get("question") or "")
        question_sha256 = text_hash(question)
        question_hash_counts[question_sha256] += 1
        indexed.append(
            {
                "record_id": str(row.get("id") or row.get("_id") or index),
                "row_index": index,
                "question_sha256": question_sha256,
            }
        )

    duplicate_questions = {
        digest: count for digest, count in question_hash_counts.items() if count > 1
    }
    if duplicate_questions:
        raise ValueError(
            "duplicate normalized questions require a grouped split before proceeding"
        )

    rng = random.Random(seed)
    rng.shuffle(indexed)
    counts = allocate_counts(len(indexed), ratios)
    split_records: dict[str, list[dict[str, Any]]] = {}
    cursor = 0
    for split_name in ratios:
        next_cursor = cursor + counts[split_name]
        split_records[split_name] = sorted(
            indexed[cursor:next_cursor], key=lambda item: item["row_index"]
        )
        cursor = next_cursor

    question_sets = {
        name: {item["question_sha256"] for item in records}
        for name, records in split_records.items()
    }
    cross_split_question_conflicts = 0
    names = list(question_sets)
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1 :]:
            cross_split_question_conflicts += len(
                question_sets[left_name] & question_sets[right_name]
            )

    manifest = {
        "schema_version": 1,
        "protocol": "query-generalization-same-corpus",
        "claim_boundary": "new questions on the same retrieval corpus",
        "seed": seed,
        "ratios": ratios,
        "counts": counts,
        "source_sha256": source_sha256,
        "label_contract": label_contract,
        "splits": split_records,
    }
    leakage_report = {
        "schema_version": 1,
        "rows": len(rows),
        "unique_question_hashes": len(question_hash_counts),
        "duplicate_question_groups": len(duplicate_questions),
        "cross_split_question_conflicts": cross_split_question_conflicts,
        "query_passage_rule": (
            "Pairs inherit the query split; train hard negatives come from train queries only."
        ),
        "verdict": (
            "pass"
            if not duplicate_questions and cross_split_question_conflicts == 0
            else "fail"
        ),
    }
    return manifest, leakage_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare locked query split artifacts")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/data"))
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--label-contract",
        required=True,
        choices=sorted(APPROVED_LABEL_CONTRACTS),
    )
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}, indent=2))
        return 2

    source_sha256 = hashlib.sha256(arrow_path.read_bytes()).hexdigest()
    manifest, leakage_report = build_split_manifest(
        read_arrow_rows(arrow_path),
        source_sha256=source_sha256,
        label_contract=args.label_contract,
        seed=args.seed,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "split_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "leakage_report.json").write_text(
        json.dumps(leakage_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"counts": manifest["counts"], **leakage_report}, indent=2))
    return 0 if leakage_report["verdict"] == "pass" else 3


if __name__ == "__main__":
    raise SystemExit(main())
