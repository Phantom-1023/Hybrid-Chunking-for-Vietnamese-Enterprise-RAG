"""
Retrieval Service Module
Thực hiện tìm kiếm ngữ nghĩa và Reranking
"""

from typing import List, Dict, Any, Optional
from src.utils import setup_logger
from src.embedding_service import EmbeddingService
from src.vector_store import QdrantVectorStore
from config.settings import settings

logger = setup_logger(__name__)


class RetrievalService:
    """Dịch vụ truy xuất thông tin"""
    
    def __init__(self, vector_store: QdrantVectorStore, embedding_service: EmbeddingService):
        """
        Khởi tạo RetrievalService
        
        Args:
            vector_store: Đối tượng quản lý vector store
            embedding_service: Đối tượng tạo embedding
        """
        self.vector_store = vector_store
        self.embedding_service = embedding_service
        self.logger = logger
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất các đoạn văn bản liên quan nhất
        
        Args:
            query: Câu hỏi của người dùng
            top_k: Số lượng kết quả trả về
            
        Returns:
            Danh sách các kết quả liên quan
        """
        if not query:
            return []
            
        self.logger.info(f"Retrieving context for query: '{query}'")
        
        # 1. Tạo embedding cho câu hỏi
        query_vector = self.embedding_service.embed_text(query)
        
        # 2. Tìm kiếm trong vector store
        raw_results = self.vector_store.search(query_vector, top_k=max(top_k * 3, top_k))
        results = self._prepare_parent_context(raw_results, top_k=top_k)
        
        self.logger.info(f"✅ Retrieved {len(results)} relevant chunks")
        return results
    
    def _prepare_parent_context(self, results: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
        """Promote child hits to parent context and deduplicate by parent/source."""
        prepared: List[Dict[str, Any]] = []
        seen = set()

        for result in results:
            score = float(result.get("score", 0.0) or 0.0)
            if score < settings.similarity_threshold:
                continue

            metadata = result.get("metadata", {}) or {}
            parent_id = result.get("parent_id") or metadata.get("parent_id") or result.get("source")
            dedupe_key = (result.get("source"), parent_id)
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            parent_content = result.get("parent_content") or metadata.get("parent_content") or result.get("content", "")
            prepared.append(
                {
                    **result,
                    "content": parent_content,
                    "matched_child": result.get("original_content") or result.get("content", ""),
                    "parent_id": parent_id,
                    "score": score,
                }
            )
            if len(prepared) >= top_k:
                break

        return prepared

    def hybrid_retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Truy xuất kết hợp (Semantic + Keyword) - Placeholder cho nâng cấp sau
        """
        # Hiện tại vẫn dùng retrieve cơ bản
        return self.retrieve(query, top_k)
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sắp xếp lại kết quả sử dụng Cross-Encoder (nếu có)
        """
        # Placeholder cho Reranking module
        return results
