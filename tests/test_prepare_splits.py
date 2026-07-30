from pathlib import Path
import sys

import pytest


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from prepare_splits import allocate_counts, build_split_manifest  # noqa: E402


def _rows(count: int):
    return [
        {
            "id": f"record-{index}",
            "question": f"Question {index}",
            "answer": f"Answer {index}",
            "context": [f"Evidence {index}", "Noise"],
        }
        for index in range(count)
    ]


def test_allocate_counts_uses_all_rows():
    assert allocate_counts(1141, {"train": 0.8, "dev": 0.1, "test": 0.1}) == {
        "train": 913,
        "dev": 114,
        "test": 114,
    }


def test_split_is_deterministic_and_has_no_question_overlap():
    first, first_report = build_split_manifest(
        _rows(20),
        source_sha256="snapshot",
        label_contract="context-zero-verified",
        seed=42,
    )
    second, second_report = build_split_manifest(
        _rows(20),
        source_sha256="snapshot",
        label_contract="context-zero-verified",
        seed=42,
    )

    assert first == second
    assert first_report == second_report
    assert first_report["cross_split_question_conflicts"] == 0
    assert first_report["verdict"] == "pass"


def test_split_fails_closed_without_label_contract():
    with pytest.raises(ValueError, match="label contract"):
        build_split_manifest(
            _rows(5),
            source_sha256="snapshot",
            label_contract="context-zero-assumed",
        )


def test_duplicate_questions_require_grouped_split():
    rows = _rows(5)
    rows[4]["question"] = rows[0]["question"]

    with pytest.raises(ValueError, match="duplicate normalized questions"):
        build_split_manifest(
            rows,
            source_sha256="snapshot",
            label_contract="context-zero-verified",
        )
