from src.knowledge.retriever import HybridRetriever
from src.models.llm_factory import LLMFactory

class ResearchAgent:
    def __init__(self):
        self.retriever = HybridRetriever()

    def process_query(self, query: str) -> dict:
        contexts = self.retriever.search(query)
        if not contexts:
            return {"answer": "Hệ thống không tìm thấy tài liệu phù hợp trong Database.", "contexts": []}
            
        context_str = "\n---\n".join(contexts)
        prompt = f"Ngữ cảnh:\n{context_str}\n\nCâu hỏi: {query}\nTrả lời:"
        
        answer = LLMFactory.generate(prompt)
        return {"answer": answer, "contexts": contexts} # Trả về dạng Dictionary