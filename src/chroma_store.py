"""
ChromaDB local storage for the 4 chunking-strategy collections.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from config.constants import CHROMA_DB_PATH


class ChromaStoreError(RuntimeError):
    """Raised when ChromaDB is unavailable or fails."""


@dataclass
class ChromaSearchResult:
    """Minimal search result for index smoke checks."""

    document: str
    metadata: Dict[str, Any]
    distance: float


class ChromaVectorStore:
    """Persistent ChromaDB wrapper scoped to local benchmark collections."""

    def __init__(self, path: str = CHROMA_DB_PATH):
        self.path = path
        try:
            import chromadb
        except ImportError as exc:
            raise ChromaStoreError(
                "Missing chromadb package. Please install dependencies from requirements.txt."
            ) from exc

        try:
            self.client = chromadb.PersistentClient(path=path)
        except Exception as exc:
            raise ChromaStoreError(f"Could not initialize ChromaDB at {path}: {exc}") from exc

    def reset_collection(self, collection_name: str):
        try:
            try:
                self.client.delete_collection(collection_name)
            except Exception:
                pass
            return self.client.get_or_create_collection(collection_name)
        except Exception as exc:
            raise ChromaStoreError(f"Could not reset collection '{collection_name}': {exc}") from exc

    def get_collection(self, collection_name: str):
        try:
            return self.client.get_or_create_collection(collection_name)
        except Exception as exc:
            raise ChromaStoreError(f"Could not open collection '{collection_name}': {exc}") from exc

    def add_embeddings(
        self,
        collection_name: str,
        ids: List[str],
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        if not ids:
            return
        try:
            collection = self.get_collection(collection_name)
            collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
        except Exception as exc:
            raise ChromaStoreError(f"Could not add embeddings to '{collection_name}': {exc}") from exc

    def count(self, collection_name: str) -> int:
        try:
            return int(self.get_collection(collection_name).count())
        except Exception as exc:
            raise ChromaStoreError(f"Could not count collection '{collection_name}': {exc}") from exc

    def query(
        self,
        collection_name: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[ChromaSearchResult]:
        try:
            collection = self.get_collection(collection_name)
            result = collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as exc:
            raise ChromaStoreError(f"Could not query collection '{collection_name}': {exc}") from exc

        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [
            ChromaSearchResult(
                document=document,
                metadata=metadata or {},
                distance=float(distance),
            )
            for document, metadata, distance in zip(documents, metadatas, distances)
        ]
