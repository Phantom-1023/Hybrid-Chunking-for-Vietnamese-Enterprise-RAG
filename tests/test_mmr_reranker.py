import numpy as np
import pytest

from src.hybrid_retriever import RankedCandidate
from src.mmr_reranker import maximal_marginal_relevance


def test_mmr_balances_relevance_and_diversity():
    candidates = [
        RankedCandidate("a", "A"),
        RankedCandidate("near-duplicate", "Near duplicate"),
        RankedCandidate("diverse", "Diverse"),
    ]
    embeddings = {
        "a": np.asarray([1.0, 0.0]),
        "near-duplicate": np.asarray([0.99, 0.01]),
        "diverse": np.asarray([0.7, 0.7]),
    }

    reranked = maximal_marginal_relevance(
        candidates,
        [1.0, 0.0],
        embeddings,
        top_k=3,
        relevance_weight=0.5,
    )

    assert reranked[0].candidate_id == "a"
    assert reranked[1].candidate_id == "diverse"


def test_mmr_validates_weight():
    with pytest.raises(ValueError, match="relevance_weight"):
        maximal_marginal_relevance([], [1.0], {}, relevance_weight=1.1)
