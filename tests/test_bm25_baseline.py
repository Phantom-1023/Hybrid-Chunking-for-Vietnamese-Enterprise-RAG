from scripts.run_bm25_baseline import build_unique_passage_corpus, run_bm25_baseline


def test_unique_corpus_deduplicates_passages():
    rows = [
        {"context": ["shared", "noise"]},
        {"context": ["shared", "other"]},
    ]

    corpus = build_unique_passage_corpus(rows)

    assert len(corpus) == 3


def test_baseline_uses_locked_test_rows_and_context_zero_positive():
    rows = [
        {
            "question": "quy định nghỉ phép",
            "context": ["quy định nghỉ phép nhân viên", "thanh toán hóa đơn"],
        },
        {
            "question": "thanh toán hóa đơn",
            "context": ["quy trình thanh toán hóa đơn", "quy định tài khoản"],
        },
    ]
    manifest = {
        "source_sha256": "snapshot",
        "label_contract": "context-zero-verified",
        "splits": {
            "test": [
                {
                    "row_index": 0,
                    "question_sha256": "question-hash",
                }
            ]
        },
    }

    result = run_bm25_baseline(rows, manifest, top_k=2)

    assert result["summary"]["queries"] == 1.0
    assert result["summary"]["hit@1"] == 1.0
    assert result["query_results"][0]["first_relevant_rank"] == 1
