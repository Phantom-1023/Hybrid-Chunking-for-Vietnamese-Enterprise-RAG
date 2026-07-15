import requests
from src.core.config import settings

class LLMFactory:
    @staticmethod
    def generate(prompt: str) -> str:
        payload = {
            "model": settings.LLM_MODEL,
            "prompt": prompt,
            "stream": False
        }
        try:
            res = requests.post(settings.OLLAMA_URL, json=payload)
            return res.json().get("response", "Lỗi LLM.")
        except Exception as e:
            return f"Lỗi kết nối Ollama: {e}"