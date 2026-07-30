"""
Minimal retrieval pipeline for querying the 4 ChromaDB strategy collections.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from config.constants import STRATEGY_COLLECTIONS
from config.settings import settings
from src.ai_gateway import EmbeddingProvider
from src.chroma_store import ChromaVectorStore
from src.reranker import CrossEncoderReranker


class RetrieverError(RuntimeError):
    """Raised when retrieval cannot run."""


@dataclass
class RetrievedChunk:
    """Retrieved source chunk returned by ChromaDB."""

    content: str
    metadata: Dict[str, Any]
    distance: float


class StrategyRetriever:
    """Embed a question and query the selected strategy collection."""

    def __init__(
        self,
        chroma_path: str = "",
        *,
        store=None,
        embedding_provider=None,
        reranker=None,
        candidate_k: int = 20,
        auto_load_reranker: bool = True,
    ):
        self.store = store or ChromaVectorStore(
            path=chroma_path or settings.chroma_db_path
        )
        self.embedding_provider = embedding_provider or EmbeddingProvider()
        self.candidate_k = candidate_k
        self.reranker = reranker
        if self.reranker is None and auto_load_reranker:
            checkpoint = Path("checkpoints/reranker/full/best")
            checksum_path = Path("artifacts/reranker/full_checkpoint.sha256")
            if checkpoint.is_dir() and checksum_path.is_file():
                expected_checksum = checksum_path.read_text(
                    encoding="utf-8"
                ).split()[0]
                self.reranker = CrossEncoderReranker(
                    checkpoint,
                    expected_sha256=expected_checksum,
                    device=settings.embedding_device,
                )

    def retrieve(self, question: str, strategy: str, top_k: int = 5) -> List[RetrievedChunk]:
        if strategy not in STRATEGY_COLLECTIONS:
            allowed = ", ".join(STRATEGY_COLLECTIONS.keys())
            raise RetrieverError(f"Unsupported strategy '{strategy}'. Allowed: {allowed}")

        collection_name = STRATEGY_COLLECTIONS[strategy]
        if self.store.count(collection_name) <= 0:
            raise RetrieverError(f"Collection '{collection_name}' is empty. Run index first.")

        query_embedding = self.embedding_provider.embed_text(question)
        retrieval_k = max(top_k, self.candidate_k) if self.reranker else top_k
        results = self.store.query(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=retrieval_k,
        )
        chunks = [
            RetrievedChunk(
                content=result.document,
                metadata=result.metadata,
                distance=result.distance,
            )
            for result in results
        ]
        if not self.reranker:
            return chunks
        reranked = self.reranker.rerank(question, chunks, top_k=top_k)
        return [
            RetrievedChunk(
                content=item.item.content,
                metadata={
                    **item.item.metadata,
                    "reranker": "fine_tuned_cross_encoder",
                    "reranker_score": item.score,
                },
                distance=item.item.distance,
            )
            for item in reranked
        ]
