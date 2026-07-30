from scripts.audit_dataset import audit_rows, content_hash, normalize_text


def test_normalize_text_is_case_and_whitespace_stable():
    assert normalize_text("  Xin   CHÀO\n") == normalize_text("xin chào")
    assert content_hash(" A  B ") == content_hash("a b")


def test_audit_reports_duplicates_without_record_text():
    rows = [
        {"question": "Câu hỏi", "answer": "Đáp án 1", "context": ["Ngữ cảnh"]},
        {"question": " câu  HỎI ", "answer": "Đáp án 2", "context": ["Ngữ cảnh"]},
    ]

    result = audit_rows(rows)

    assert result["rows"] == 2
    assert result["exact_duplicate_audit"]["question"]["duplicate_rows_beyond_first"] == 1
    assert result["exact_duplicate_audit"]["individual_context_passage"][
        "duplicate_rows_beyond_first"
    ] == 1
    assert result["record_groups_by_shared_context"]["groups"] == 1
    assert result["record_groups_by_shared_context"]["largest_group_rows"] == 2
    assert "Câu hỏi" not in str(result)
