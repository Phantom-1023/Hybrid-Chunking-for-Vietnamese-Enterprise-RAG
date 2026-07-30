"""Prepare leakage-safe Cross-Encoder groups from the locked split manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_dataset import locate_default_arrow, normalize_text, read_arrow_rows


def _hash(value: str) -> str:
    return hashlib.sha256(normalize_text(value).encode("utf-8")).hexdigest()


def _pair_hash(question: str, passage: str) -> str:
    return hashlib.sha256(
        f"{normalize_text(question)}\0{normalize_text(passage)}".encode("utf-8")
    ).hexdigest()


def prepare_groups(
    rows: list[dict[str, Any]],
    split_manifest: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, Any]]:
    if split_manifest.get("label_contract") != "context-zero-verified":
        raise ValueError("context-zero label contract is not verified")

    groups_by_split: dict[str, list[dict[str, Any]]] = {}
    pair_hashes_by_split: dict[str, set[str]] = {}
    stats: dict[str, Any] = {}

    for split_name, entries in split_manifest["splits"].items():
        groups: list[dict[str, Any]] = []
        pair_hashes: set[str] = set()
        negative_count = 0
        multiple_positive_exclusions = 0
        duplicate_negative_exclusions = 0

        for entry in entries:
            row_index = int(entry["row_index"])
            row = rows[row_index]
            question = str(row.get("question") or "")
            answer = str(row.get("answer") or "")
            contexts = [str(context) for context in (row.get("context") or [])]
            if len(contexts) < 2:
                raise ValueError(f"row {row_index} does not contain positive+negative contexts")

            positive = contexts[0]
            positive_hash = _hash(positive)
            normalized_answer = normalize_text(answer)
            seen_negative_hashes: set[str] = set()
            negatives: list[str] = []
            for candidate in contexts[1:]:
                candidate_hash = _hash(candidate)
                if candidate_hash == positive_hash or candidate_hash in seen_negative_hashes:
                    duplicate_negative_exclusions += 1
                    continue
                if normalized_answer and normalized_answer in normalize_text(candidate):
                    multiple_positive_exclusions += 1
                    continue
                seen_negative_hashes.add(candidate_hash)
                negatives.append(candidate)

            if not negatives:
                raise ValueError(f"row {row_index} has no defensible negatives")

            pair_hashes.add(_pair_hash(question, positive))
            pair_hashes.update(_pair_hash(question, negative) for negative in negatives)
            negative_count += len(negatives)
            groups.append(
                {
                    "row_index": row_index,
                    "question": question,
                    "positive": positive,
                    "negatives": negatives,
                }
            )

        groups_by_split[split_name] = groups
        pair_hashes_by_split[split_name] = pair_hashes
        stats[split_name] = {
            "queries": len(groups),
            "positive_pairs": len(groups),
            "negative_pairs": negative_count,
            "multiple_positive_exclusions": multiple_positive_exclusions,
            "duplicate_negative_exclusions": duplicate_negative_exclusions,
            "pair_hashes": len(pair_hashes),
        }

    conflicts: dict[str, int] = {}
    split_names = list(pair_hashes_by_split)
    for left_index, left_name in enumerate(split_names):
        for right_name in split_names[left_index + 1 :]:
            key = f"{left_name}_vs_{right_name}"
            conflicts[key] = len(
                pair_hashes_by_split[left_name] & pair_hashes_by_split[right_name]
            )
    if any(conflicts.values()):
        raise ValueError(f"query-passage leakage detected: {conflicts}")

    manifest = {
        "schema_version": 1,
        "strategy": "in-record-negatives-v1",
        "label_contract": split_manifest["label_contract"],
        "split_source_sha256": split_manifest["source_sha256"],
        "splits": stats,
        "cross_split_pair_conflicts": conflicts,
        "hard_negative_rule": "Only train queries may be used for train hard-negative mining.",
        "claim_boundary": "Initial supervised pairs; hard negatives are added after first-stage retrieval is frozen.",
    }
    return groups_by_split, manifest


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare Cross-Encoder pair groups")
    parser.add_argument("--arrow", type=Path, help="Explicit Arrow snapshot path")
    parser.add_argument(
        "--split-manifest",
        type=Path,
        default=Path("artifacts/data/split_manifest.json"),
    )
    parser.add_argument(
        "--groups-dir",
        type=Path,
        default=Path(".cache/reranker/groups"),
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=Path("artifacts/reranker/pair_manifest.json"),
    )
    args = parser.parse_args()

    arrow_path = args.arrow or locate_default_arrow()
    if arrow_path is None or not arrow_path.is_file():
        print(json.dumps({"error": "Vietnamese_RAG Arrow snapshot not found"}, indent=2))
        return 2
    if not args.split_manifest.is_file():
        print(json.dumps({"error": "locked split manifest not found"}, indent=2))
        return 2

    split_manifest = json.loads(args.split_manifest.read_text(encoding="utf-8"))
    groups_by_split, manifest = prepare_groups(
        read_arrow_rows(arrow_path),
        split_manifest,
    )
    for split_name, groups in groups_by_split.items():
        _write_jsonl(args.groups_dir / f"{split_name}.jsonl", groups)

    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
