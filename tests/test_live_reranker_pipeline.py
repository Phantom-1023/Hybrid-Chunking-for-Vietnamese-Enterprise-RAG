from dataclasses import dataclass

from src.reranker import CrossEncoderReranker
from src.retriever import StrategyRetriever


@dataclass
class _StoreResult:
    document: str
    metadata: dict
    distance: float


class _Store:
    def __init__(self):
        self.requested_top_k = None

    def count(self, _collection):
        return 20

    def query(self, *, collection_name, query_embedding, top_k):
        self.requested_top_k = top_k
        return [
            _StoreResult(
                document=f"passage {index}",
                metadata={"index": index},
                distance=float(index),
            )
            for index in range(top_k)
        ]


class _EmbeddingProvider:
    def embed_text(self, _question):
        return [0.0]


class _PredictModel:
    def predict(self, pairs, **_kwargs):
        return [float(pair[1].split()[-1]) for pair in pairs]


def test_live_pipeline_retrieves_twenty_then_returns_five_reranked_items():
    store = _Store()
    reranker = CrossEncoderReranker(
        "unused",
        model=_PredictModel(),
    )
    retriever = StrategyRetriever(
        store=store,
        embedding_provider=_EmbeddingProvider(),
        reranker=reranker,
        candidate_k=20,
        auto_load_reranker=False,
    )

    results = retriever.retrieve("question", "paragraph", top_k=5)

    assert store.requested_top_k == 20
    assert [item.content for item in results] == [
        "passage 19",
        "passage 18",
        "passage 17",
        "passage 16",
        "passage 15",
    ]
    assert all(
        item.metadata["reranker"] == "fine_tuned_cross_encoder"
        for item in results
    )
