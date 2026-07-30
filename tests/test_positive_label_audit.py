from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from audit_positive_labels import (  # noqa: E402
    answer_token_recall,
    audit_positive_labels,
    exact_match_positions,
)


def test_exact_match_positions_normalize_case_and_space():
    assert exact_match_positions(
        "Chính sách nghỉ phép",
        ["Không liên quan", "  CHÍNH SÁCH   NGHỈ PHÉP áp dụng từ 2026."],
    ) == [1]


def test_answer_token_recall_is_diagnostic():
    assert answer_token_recall("alpha beta", "alpha gamma") == 0.5


def test_audit_keeps_unresolved_rows_out_of_exact_labels():
    rows = [
        {"answer": "alpha", "context": ["alpha evidence", "noise"]},
        {"answer": "beta", "context": ["noise", "beta evidence"]},
        {"answer": "gamma delta", "context": ["gamma only", "noise"]},
    ]

    result = audit_positive_labels(rows)

    assert result["exact_match"]["context_zero_rows"] == 1
    assert result["exact_match"]["only_later_context_rows"] == 1
    assert result["exact_match"]["unresolved_rows"] == 1
    assert result["exact_match"]["position_counts"] == {0: 1, 1: 1}
