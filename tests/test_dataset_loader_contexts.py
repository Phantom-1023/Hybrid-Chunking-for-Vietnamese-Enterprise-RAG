from src.dataset_loader import _normalize_record, context_parts, join_context


def test_context_parts_preserve_order_and_clean_spaces():
    assert context_parts(["  first  passage ", {"text": "second\tpassage"}]) == [
        "first passage",
        "second passage",
    ]


def test_normalized_record_keeps_contexts_and_joined_context():
    record = _normalize_record(
        {
            "id": "row-1",
            "question": "Question",
            "answer": "Answer",
            "context": ["positive", "negative"],
        },
        0,
    )

    assert record.contexts == ["positive", "negative"]
    assert record.joined_context == "positive\n\nnegative"
    assert join_context(record.contexts) == record.joined_context
