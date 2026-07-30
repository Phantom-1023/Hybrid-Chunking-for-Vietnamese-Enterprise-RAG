import pytest

from src.retrieval_metrics import aggregate_query_metrics, evaluate_query_ranking


def test_single_positive_metrics_use_passage_id_not_record_id():
    metrics = evaluate_query_ranking(["noise", "positive", "other"], {"positive"})

    assert metrics.first_relevant_rank == 2
    assert metrics.hit_at[1] == 0.0
    assert metrics.hit_at[3] == 1.0
    assert metrics.reciprocal_rank == 0.5
    assert metrics.ndcg_at[5] > 0


def test_missing_positive_scores_zero():
    metrics = evaluate_query_ranking(["noise"], {"positive"})

    assert metrics.first_relevant_rank is None
    assert metrics.reciprocal_rank == 0.0
    assert metrics.recall_at[20] == 0.0


def test_aggregate_metrics_average_queries():
    metrics = [
        evaluate_query_ranking(["positive"], {"positive"}),
        evaluate_query_ranking(["noise"], {"positive"}),
    ]

    summary = aggregate_query_metrics(metrics)

    assert summary["queries"] == 2.0
    assert summary["mrr"] == 0.5
    assert summary["hit@1"] == 0.5


def test_relevant_ids_are_required():
    with pytest.raises(ValueError, match="relevant_ids"):
        evaluate_query_ranking([], set())
