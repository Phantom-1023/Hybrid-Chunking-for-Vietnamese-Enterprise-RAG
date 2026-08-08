from src.knowledge.retriever import HybridRetriever
from src.models.llm_factory import LLMFactory
from sentence_transformers import CrossEncoder

# Khởi tạo Reranker
try:
    reranker = CrossEncoder('BAAI/bge-reranker-v2-m3')
except Exception as e:
    print(f"Lỗi load Reranker: {e}")
    reranker = None

class ResearchAgent:
    def __init__(self):
        # GIỮ NGUYÊN HOÀN TOÀN CODE CŨ CỦA BẠN
        self.retriever = HybridRetriever()

    def expand_query(self, query):
        """Mở rộng từ khóa viết tắt thường gặp"""
        replacements = {
            "bhxh": "bảo hiểm xã hội",
            "kpi": "chỉ số đánh giá hiệu quả công việc",
            "hđlđ": "hợp đồng lao động",
            "nsnn": "ngân sách nhà nước"
        }
        expanded = query.lower()
        for short, full in replacements.items():
            expanded = expanded.replace(short, full)
        return expanded

    def retrieve_and_rerank(self, query, top_k=3):
        """Pipeline tìm kiếm nâng cao: Expand -> Hybrid Search -> Rerank"""
        refined_query = self.expand_query(query)
        
        # 1. Gọi hàm search từ class cũ của bạn (Trả về list các chuỗi văn bản)
        raw_contexts = self.retriever.search(refined_query)
        
        # Nếu không tìm thấy gì hoặc Reranker bị lỗi, trả về kết quả gốc
        if not raw_contexts or not reranker:
            return raw_contexts[:top_k] if raw_contexts else []

        # 2. Reranker chấm điểm lại độ liên quan (Xử lý trực tiếp list string)
        pairs = [[refined_query, text] for text in raw_contexts]
        scores = reranker.predict(pairs)
        
        # 3. Ghép điểm số vào text và sắp xếp lại từ cao xuống thấp
        scored_contexts = list(zip(raw_contexts, scores))
        scored_contexts.sort(key=lambda x: x[1], reverse=True)
        
        # 4. Trả về Top K tài liệu (chỉ lấy phần văn bản)
        best_contexts = [context for context, score in scored_contexts[:top_k]]
        return best_contexts

    def process_query(self, query: str) -> dict:
        # Lấy tài liệu đã qua xử lý nâng cao (Thay vì gọi self.retriever trực tiếp như cũ)
        best_contexts = self.retrieve_and_rerank(query)
        
        if not best_contexts:
            return {"answer": "Hệ thống không tìm thấy tài liệu phù hợp trong Database.", "contexts": []}
            
        # Gộp tài liệu lại (Đúng logic cũ của bạn)
        context_str = "\n---\n".join(best_contexts)
        
        # Sử dụng đúng format prompt mà bạn dùng để Train mô hình RAG
        prompt = f"Dựa vào các tài liệu sau đây:\n{context_str}\n\nHãy trả lời câu hỏi: {query}"
        
        # Gọi LLMFactory giống hệt code cũ
        answer = LLMFactory.generate(prompt)
        
        # Trả về đúng format Dictionary cũ để FE không bị lỗi
        return {"answer": answer, "contexts": best_contexts}