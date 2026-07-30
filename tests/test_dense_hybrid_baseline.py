from pathlib import Path

import numpy as np

from scripts.run_bm25_baseline import build_unique_passage_corpus
from scripts.run_dense_hybrid_baseline import (
    corpus_hash,
    load_or_encode_corpus,
    write_comparison_csv,
)


class FakeE5:
    model_name = "fake-e5"

    def __init__(self):
        self.calls = 0

    def encode_passages(self, passages, *, batch_size):
        self.calls += 1
        return np.eye(len(passages), dtype=np.float32)


def test_embedding_cache_is_reused(tmp_path: Path):
    documents = build_unique_passage_corpus(
        [{"context": ["alpha", "beta"]}]
    )
    model = FakeE5()
    cache_path = tmp_path / "embeddings.npz"

    first, first_hit, first_hash = load_or_encode_corpus(
        model,
        documents,
        cache_path=cache_path,
        batch_size=2,
    )
    second, second_hit, second_hash = load_or_encode_corpus(
        model,
        documents,
        cache_path=cache_path,
        batch_size=2,
    )

    assert first_hit is False
    assert second_hit is True
    assert first_hash == second_hash == corpus_hash(
        [document.document_id for document in documents]
    )
    assert np.array_equal(first, second)
    assert model.calls == 1


def test_comparison_csv_has_all_methods(tmp_path: Path):
    summary = {
        "queries": 1.0,
        "recall@20": 1.0,
        "hit@1": 1.0,
        "hit@3": 1.0,
        "hit@5": 1.0,
        "mrr": 1.0,
        "ndcg@10": 1.0,
        "latency_p50_ms": 1.0,
        "latency_p95_ms": 2.0,
    }
    result = {
        "corpus_passages": 2,
        "summaries": {
            "dense": summary,
            "bm25": summary,
            "hybrid_rrf": summary,
        },
    }
    output = tmp_path / "comparison.csv"

    write_comparison_csv(result, output)

    rendered = output.read_text(encoding="utf-8")
    assert "dense" in rendered
    assert "bm25" in rendered
    assert "hybrid_rrf" in rendered
