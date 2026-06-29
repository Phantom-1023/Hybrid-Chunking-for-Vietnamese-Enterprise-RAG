"""
RAG Pipeline Module
Connects retrieval and generation with grounded Vietnamese prompts.
"""

from typing import Dict, Any

from src.utils import setup_logger
from src.retrieval_service import RetrievalService
from src.llm_service import LLMService

logger = setup_logger(__name__)


class RAGPipeline:
    """End-to-end Retrieval-Augmented Generation pipeline."""

    def __init__(self, retrieval_service: RetrievalService, llm_service: LLMService):
        self.retrieval_service = retrieval_service
        self.llm_service = llm_service
        self.logger = logger
        self.system_prompt = (
            "Bạn là trợ lý tri thức nội bộ cho doanh nghiệp Việt Nam. "
            "Chỉ trả lời dựa trên CONTEXT được cung cấp. "
            "Nếu context không chứa đủ thông tin, hãy nói rõ là chưa tìm thấy đủ dữ liệu trong kho tri thức. "
            "Không tự suy diễn, không bịa số liệu, và luôn trả lời bằng tiếng Việt chuyên nghiệp, ngắn gọn."
        )

    def ask(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        relevant_chunks = self.retrieval_service.retrieve(query, top_k=top_k)

        if not relevant_chunks:
            return {
                "answer": "Mình chưa tìm thấy đủ thông tin liên quan trong kho tri thức để trả lời câu hỏi này.",
                "sources": [],
            }

        context_text = "\n\n".join(
            [
                (
                    f"[Nguồn {i + 1}] File: {res.get('source', 'unknown')} | "
                    f"Score: {res.get('score', 0):.3f}\n"
                    f"{res.get('content', '')}"
                )
                for i, res in enumerate(relevant_chunks)
            ]
        )

        prompt = (
            "Dựa trên CONTEXT dưới đây, hãy trả lời câu hỏi của người dùng.\n"
            "Yêu cầu:\n"
            "- Trả lời đúng trọng tâm, bằng tiếng Việt.\n"
            "- Nếu thiếu thông tin trong CONTEXT, nói rõ chưa tìm thấy đủ dữ liệu.\n"
            "- Cuối câu trả lời ghi mục 'Nguồn tham khảo' với tên file liên quan.\n\n"
            f"CONTEXT:\n{context_text}\n\n"
            f"CÂU HỎI: {query}\n\n"
            "TRẢ LỜI:"
        )

        self.logger.info("Generating grounded answer using LLM...")
        answer = self.llm_service.generate_response(prompt, self.system_prompt)

        return {
            "answer": answer,
            "sources": [
                {
                    "source": res.get("source", ""),
                    "content": res.get("content", ""),
                    "matched_child": res.get("matched_child", ""),
                    "score": res.get("score", 0.0),
                    "metadata": res.get("metadata", {}),
                }
                for res in relevant_chunks
            ],
        }
