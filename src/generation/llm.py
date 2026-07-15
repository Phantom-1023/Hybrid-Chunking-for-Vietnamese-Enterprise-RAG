import requests, os
from dotenv import load_dotenv

load_dotenv()

def generate_answer(query: str, contexts: list) -> str:
    if not contexts: return "Hệ thống không tìm thấy tài liệu phù hợp."
    
    url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")
    model = os.getenv("LLM_MODEL_NAME", "business-qwen")
    
    context_str = "\n---\n".join(contexts)
    prompt = f"Ngữ cảnh:\n{context_str}\n\nCâu hỏi: {query}\nTrả lời:"

    try:
        res = requests.post(url, json={"model": model, "prompt": prompt, "stream": False})
        return res.json().get("response", "Lỗi sinh văn bản.")
    except Exception as e:
        return f"Lỗi gọi Ollama: {e}"