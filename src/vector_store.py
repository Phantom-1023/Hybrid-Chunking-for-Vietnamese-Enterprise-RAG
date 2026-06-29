"""
Vector Store Module
Qdrant integration with a local-memory fallback for reliable demos.
"""

from typing import List, Dict, Any
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from src.utils import setup_logger
from config.settings import settings

logger = setup_logger(__name__)


class QdrantVectorStore:
    """Store and search document vectors in Qdrant or local memory."""

    def __init__(self, collection_name: str = "enterprise_knowledge"):
        self.logger = logger
        self.collection_name = collection_name
        self.local_storage: List[Dict[str, Any]] = []

        try:
            self.client = QdrantClient(
                host=settings.qdrant_host,
                port=settings.qdrant_port,
                api_key=settings.qdrant_api_key or None,
            )
            self.client.get_collections()
            self.logger.info(f"Connected to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")
        except Exception as e:
            self.logger.warning(f"Could not connect to Qdrant, using local memory fallback: {e}")
            self.client = None

    def create_collection(self, vector_size: int, distance=models.Distance.COSINE) -> None:
        if not self.client or not vector_size:
            return

        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            if exists:
                return

            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=vector_size, distance=distance),
            )
            self.logger.info(f"Created collection '{self.collection_name}' with vector size {vector_size}")
        except Exception as e:
            self.logger.error(f"Error creating collection: {e}")

    def add_documents(self, chunks: List[Any], embeddings: List[List[float]]) -> None:
        if not chunks or not embeddings:
            return
        if len(chunks) != len(embeddings):
            self.logger.error("Mismatch between chunks and embeddings count")
            return

        valid_pairs = [(chunk, vector) for chunk, vector in zip(chunks, embeddings) if vector]
        if not valid_pairs:
            self.logger.error("No valid embeddings to index")
            return

        if self.client:
            try:
                self.create_collection(vector_size=len(valid_pairs[0][1]))
                points = [
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=vector,
                        payload=self._chunk_to_payload(chunk),
                    )
                    for chunk, vector in valid_pairs
                ]
                for i in range(0, len(points), 100):
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=points[i:i + 100],
                    )
                self.logger.info(f"Successfully added {len(points)} points to Qdrant")
                return
            except Exception as e:
                self.logger.error(f"Error adding documents to Qdrant, falling back to memory: {e}")

        for chunk, vector in valid_pairs:
            self.local_storage.append(
                {
                    "vector": vector,
                    "payload": self._chunk_to_payload(chunk),
                }
            )
        self.logger.info(f"Added {len(valid_pairs)} points to local memory storage")

    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        if not query_vector:
            return []

        if self.client:
            try:
                search_result = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    limit=top_k,
                    with_payload=True,
                )
                return [self._result_from_payload(res.payload or {}, float(res.score)) for res in search_result]
            except Exception as e:
                self.logger.error(f"Error searching in Qdrant: {e}")

        return self._search_local(query_vector, top_k)

    def _search_local(self, query_vector: List[float], top_k: int) -> List[Dict[str, Any]]:
        import numpy as np

        def cosine_similarity(v1, v2) -> float:
            v1 = np.asarray(v1, dtype=float)
            v2 = np.asarray(v2, dtype=float)
            norm = np.linalg.norm(v1) * np.linalg.norm(v2)
            if norm == 0:
                return 0.0
            return float(np.dot(v1, v2) / norm)

        scored_results = [
            self._result_from_payload(item["payload"], cosine_similarity(query_vector, item["vector"]))
            for item in self.local_storage
        ]
        scored_results.sort(key=lambda x: x["score"], reverse=True)
        return scored_results[:top_k]

    def _chunk_to_payload(self, chunk: Any) -> Dict[str, Any]:
        metadata = getattr(chunk, "metadata", {}) or {}
        content = getattr(chunk, "content", getattr(chunk, "original_content", ""))
        original_content = getattr(chunk, "original_content", content)
        source = getattr(chunk, "source_document", metadata.get("source_document", "unknown"))
        chunk_index = getattr(chunk, "chunk_index", metadata.get("chunk_index", 0))

        return {
            "content": content,
            "source": source,
            "chunk_index": chunk_index,
            "metadata": metadata,
            "original_content": original_content,
            "parent_content": metadata.get("parent_content", original_content),
            "parent_id": metadata.get("parent_id", getattr(chunk, "chunk_id", "")),
        }

    def _result_from_payload(self, payload: Dict[str, Any], score: float) -> Dict[str, Any]:
        return {
            "content": payload.get("content", ""),
            "source": payload.get("source", ""),
            "score": score,
            "metadata": payload.get("metadata", {}),
            "original_content": payload.get("original_content", ""),
            "parent_content": payload.get("parent_content", ""),
            "parent_id": payload.get("parent_id", ""),
        }

    def delete_collection(self) -> None:
        if self.client:
            try:
                self.client.delete_collection(collection_name=self.collection_name)
                self.logger.info(f"Deleted collection '{self.collection_name}'")
            except Exception as e:
                self.logger.error(f"Error deleting collection: {e}")
        self.local_storage.clear()

    def get_collection_info(self) -> Dict[str, Any]:
        if not self.client:
            return {
                "status": "local_memory",
                "points_count": len(self.local_storage),
                "vectors_count": len(self.local_storage),
                "config": {},
            }

        try:
            info = self.client.get_collection(collection_name=self.collection_name)
            return {
                "status": info.status,
                "points_count": info.points_count,
                "vectors_count": getattr(info, "vectors_count", info.points_count),
                "config": info.config,
            }
        except Exception as e:
            self.logger.error(f"Error getting collection info: {e}")
            return {}

    def count_documents(self) -> int:
        info = self.get_collection_info()
        return int(info.get("points_count") or 0)

    def get_backend_name(self) -> str:
        return "Qdrant" if self.client else "Local memory fallback"
