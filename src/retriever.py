"""
Minimal retrieval pipeline for querying the 4 ChromaDB strategy collections.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from config.constants import STRATEGY_COLLECTIONS
from config.settings import settings
from src.ai_gateway import EmbeddingProvider
from src.chroma_store import ChromaVectorStore


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

    def __init__(self, chroma_path: str = ""):
        self.store = ChromaVectorStore(path=chroma_path or settings.chroma_db_path)
        self.embedding_provider = EmbeddingProvider()

    def retrieve(self, question: str, strategy: str, top_k: int = 5) -> List[RetrievedChunk]:
        if strategy not in STRATEGY_COLLECTIONS:
            allowed = ", ".join(STRATEGY_COLLECTIONS.keys())
            raise RetrieverError(f"Unsupported strategy '{strategy}'. Allowed: {allowed}")

        collection_name = STRATEGY_COLLECTIONS[strategy]
        if self.store.count(collection_name) <= 0:
            raise RetrieverError(f"Collection '{collection_name}' is empty. Run index first.")

        query_embedding = self.embedding_provider.embed_text(question)
        results = self.store.query(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=top_k,
        )
        return [
            RetrievedChunk(
                content=result.document,
                metadata=result.metadata,
                distance=result.distance,
            )
            for result in results
        ]
