from scripts.evaluate_rerankers import build_error_analysis


def test_error_analysis_tracks_before_after_transitions():
    result = {
        "evidence_k": 5,
        "query_results": [
            {
                "row_index": 1,
                "question_sha256": "a",
                "methods": {
                    "base_cross_encoder": {"first_relevant_rank": 7},
                    "fine_tuned_cross_encoder": {"first_relevant_rank": 2},
                },
            },
            {
                "row_index": 2,
                "question_sha256": "b",
                "methods": {
                    "base_cross_encoder": {"first_relevant_rank": 1},
                    "fine_tuned_cross_encoder": {"first_relevant_rank": None},
                },
            },
        ],
    }

    analysis = build_error_analysis(result)

    assert analysis["transitions"] == {
        "miss_to_hit": 1,
        "hit_to_miss": 1,
    }
    assert len(analysis["changed_rank_examples_by_transition"]["miss_to_hit"]) == 1
    assert len(analysis["changed_rank_examples_by_transition"]["hit_to_miss"]) == 1
    assert analysis["residual_fine_tuned_misses"][0]["row_index"] == 2
