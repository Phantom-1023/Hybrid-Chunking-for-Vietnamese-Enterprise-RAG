from scripts.analyze_reranker_statistics import analyze, paired_bootstrap


def _query(before, after, *, candidate_contains=True):
    positive = "positive"
    return {
        "positive_passage_sha256": positive,
        "candidate_ids": [positive] if candidate_contains else ["noise"],
        "methods": {
            "no_rerank": {"first_relevant_rank": before},
            "base_cross_encoder": {"first_relevant_rank": before},
            "fine_tuned_cross_encoder": {"first_relevant_rank": after},
        },
    }


def test_paired_bootstrap_is_deterministic_and_paired():
    queries = [_query(8, 1), _query(1, 1), _query(None, 3)]
    first = paired_bootstrap(
        queries,
        treatment="fine_tuned_cross_encoder",
        control="base_cross_encoder",
        score=lambda rank: float(rank == 1),
        resamples=1000,
        seed=7,
    )
    second = paired_bootstrap(
        queries,
        treatment="fine_tuned_cross_encoder",
        control="base_cross_encoder",
        score=lambda rank: float(rank == 1),
        resamples=1000,
        seed=7,
    )

    assert first == second
    assert first["observed_delta"] == 1 / 3


def test_analysis_separates_rerank_failure_from_candidate_retrieval_miss():
    result = {
        "schema_version": 1,
        "candidate_source": "dense_top20_plus_bm25_top20_rrf_k60",
        "corpus_passages": 3,
        "evidence_k": 5,
        "query_results": [
            _query(8, 2),
            _query(1, 8),
            _query(None, None, candidate_contains=False),
        ],
    }

    output = analyze(result, resamples=1000, seed=7)

    taxonomy = output["error_taxonomy_base_to_fine_tuned"]
    assert taxonomy["miss_to_hit"] == 1
    assert taxonomy["hit_to_miss"] == 1
    assert taxonomy["retrieval_miss"] == 1
    assert taxonomy["candidate_positive_but_treatment_outside_top5"] == 1
