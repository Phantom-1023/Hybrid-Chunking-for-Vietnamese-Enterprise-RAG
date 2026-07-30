import numpy as np
import pytest

from src.bm25_retriever import LexicalDocument
from src.dense_retriever import DensePassageIndex
from src.local_embedding import LocalE5EmbeddingModel


class FakeSentenceTransformer:
    def __init__(self):
        self.calls = []

    def encode(self, values, **kwargs):
        self.calls.append((values, kwargs))
        return np.ones((len(values), 2), dtype=np.float32)


def test_e5_wrapper_applies_query_and_passage_prefixes():
    fake = FakeSentenceTransformer()
    model = LocalE5EmbeddingModel(model=fake)

    model.encode_queries(["câu hỏi"])
    model.encode_passages(["bằng chứng"])

    assert fake.calls[0][0] == ["query: câu hỏi"]
    assert fake.calls[1][0] == ["passage: bằng chứng"]
    assert fake.calls[0][1]["normalize_embeddings"] is True


def test_dense_index_ranks_highest_dot_product_first():
    documents = [
        LexicalDocument("a", "A"),
        LexicalDocument("b", "B"),
        LexicalDocument("c", "C"),
    ]
    embeddings = np.asarray([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]])
    index = DensePassageIndex(documents, embeddings)

    results = index.retrieve([1.0, 0.0], top_k=2)

    assert [result.document.document_id for result in results] == ["a", "c"]


def test_dense_index_rejects_mismatched_shapes():
    with pytest.raises(ValueError, match="counts"):
        DensePassageIndex([LexicalDocument("a", "A")], np.zeros((2, 3)))
