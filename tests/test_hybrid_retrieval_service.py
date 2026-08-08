from pathlib import Path

import numpy as np

from src.bm25_retriever import LexicalDocument
from src.hybrid_retriever import HybridRetriever, HybridResult


class _FakeEmbedding:
    model_name = "synthetic-embedding-v1"

    def __init__(self):
        self.passage_calls = []
        self.query_calls = []

    @staticmethod
    def _vector(text: str) -> list[float]:
        lowered = text.casefold()
        if "hr" in lowered or "nghỉ phép" in lowered:
            return [1.0, 0.0]
        if "finance" in lowered or "hóa đơn" in lowered:
            return [0.0, 1.0]
        return [0.7, 0.7]

    def encode_passages(self, passages, *, batch_size):
        values = list(passages)
        self.passage_calls.append((values, batch_size))
        return np.asarray([self._vector(value) for value in values], dtype=np.float32)

    def encode_queries(self, queries, *, batch_size):
        values = list(queries)
        self.query_calls.append((values, batch_size))
        return np.asarray([self._vector(value) for value in values], dtype=np.float32)


class _SpyReranker:
    def __init__(self):
        self.seen_ids = []

    def rerank(self, _question, items, *, top_k):
        self.seen_ids = [item.candidate_id for item in items]
        return [
            type("Reranked", (), {"item": item, "score": 0.95 - index / 100})()
            for index, item in enumerate(items[:top_k])
        ]


def _documents():
    return [
        LexicalDocument("hr-1", "HR policy: nghỉ phép năm", {"document_id": "doc-hr"}),
        LexicalDocument("finance-1", "Finance policy: hóa đơn", {"document_id": "doc-finance"}),
        LexicalDocument("ops-1", "Operations handbook", {"document_id": "doc-ops"}),
    ]


def test_acl_filtered_documents_are_the_only_dense_inputs(tmp_path: Path):
    embedding = _FakeEmbedding()
    retriever = HybridRetriever(
        embedding_model=embedding,
        cache_path=tmp_path / "embeddings.npz",
        candidate_k=20,
    )

    results = retriever.retrieve("HR nghỉ phép", [_documents()[0]], top_k=5)

    assert [result.document.document_id for result in results] == ["hr-1"]
    assert results[0].source_ranks == {"bm25": 1, "dense": 1}
    assert embedding.passage_calls == [(["HR policy: nghỉ phép năm"], 32)]
    assert all(
        "Finance" not in value
        for batch, _ in embedding.passage_calls
        for value in batch
    )


def test_embedding_cache_avoids_reencoding_existing_allowed_chunks(tmp_path: Path):
    embedding = _FakeEmbedding()
    retriever = HybridRetriever(
        embedding_model=embedding,
        cache_path=tmp_path / "embeddings.npz",
    )
    documents = _documents()

    retriever.retrieve("HR nghỉ phép", documents, top_k=2)
    retriever.retrieve("HR nghỉ phép", documents, top_k=2)

    assert len(embedding.passage_calls) == 1
    assert len(embedding.query_calls) == 2


def test_reranker_receives_only_fused_candidates_and_keeps_metadata(tmp_path: Path):
    reranker = _SpyReranker()
    retriever = HybridRetriever(
        embedding_model=_FakeEmbedding(),
        reranker=reranker,
        cache_path=tmp_path / "embeddings.npz",
        candidate_k=2,
    )

    results = retriever.retrieve("HR nghỉ phép", _documents(), top_k=1)

    assert len(reranker.seen_ids) == 2
    assert isinstance(results[0], HybridResult)
    assert results[0].method == "hybrid_rrf_then_fine_tuned_cross_encoder"
    assert results[0].document.metadata["document_id"] == "doc-hr"
