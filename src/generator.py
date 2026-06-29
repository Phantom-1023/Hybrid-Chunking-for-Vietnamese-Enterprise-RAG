"""
Minimal answer generation with graceful retrieval-only fallback.
"""

from typing import List
import requests

from config.settings import settings
from src.gemini_service import GeminiGenerationError, GeminiService, MissingGeminiApiKey
from src.retriever import RetrievedChunk


RETRIEVAL_ONLY_MESSAGE = "LLM generation unavailable; showing retrieved source chunks only."


class AnswerGenerator:
    """Generate an answer from retrieved chunks, with provider fallback."""

    def generate(self, question: str, chunks: List[RetrievedChunk]) -> str:
        prompt = self._build_prompt(question, chunks)

        try:
            return GeminiService().generate_text(prompt)
        except (MissingGeminiApiKey, GeminiGenerationError):
            pass

        if settings.deepseek_api_key:
            try:
                return self._generate_deepseek(prompt)
            except Exception:
                pass

        return RETRIEVAL_ONLY_MESSAGE

    def _build_prompt(self, question: str, chunks: List[RetrievedChunk]) -> str:
        context = "\n\n".join(
            f"[Nguồn {index + 1}]\n{chunk.content}"
            for index, chunk in enumerate(chunks)
        )
        return (
            "Bạn là trợ lý RAG trả lời bằng tiếng Việt. "
            "Chỉ dùng thông tin trong CONTEXT. Nếu thiếu dữ liệu, nói rõ là chưa đủ dữ liệu.\n\n"
            f"CONTEXT:\n{context}\n\n"
            f"CÂU HỎI: {question}\n\n"
            "TRẢ LỜI:"
        )

    def _generate_deepseek(self, prompt: str) -> str:
        response = requests.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 800,
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
