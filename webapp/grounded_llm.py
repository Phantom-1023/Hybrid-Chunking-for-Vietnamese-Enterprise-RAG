"""Server-side DeepSeek adapter for evidence-grounded answers."""

from __future__ import annotations

import os
from typing import Any

import httpx


class GroundedLLM:
    def __init__(self, *, client: httpx.Client | None = None) -> None:
        self.api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.client = client or httpx.Client(timeout=35)

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def answer(self, *, question: str, citations: list[dict[str, Any]]) -> str:
        if not self.configured:
            return "Chưa cấu hình chatbot. Dưới đây là các đoạn nguồn phù hợp nhất."
        evidence = "\n\n".join(
            f"[{index}] {citation['title']} — {citation.get('locator') or 'Nội dung'}\n"
            f"{citation['excerpt'][:1400]}"
            for index, citation in enumerate(citations, start=1)
        )
        prompt = (
            "Trả lời ngắn gọn bằng tiếng Việt chỉ từ EVIDENCE. "
            "Không suy đoán, không dùng kiến thức bên ngoài. "
            "Nếu thiếu bằng chứng, nói rõ không tìm thấy. "
            "Mỗi ý quan trọng phải gắn [số nguồn].\n\n"
            f"EVIDENCE:\n{evidence}\n\nCÂU HỎI: {question}"
        )
        try:
            response = self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "temperature": 0.1,
                    "max_tokens": 700,
                    "messages": [
                        {"role": "system", "content": "You are a careful enterprise RAG assistant."},
                        {"role": "user", "content": prompt},
                    ],
                },
            )
            response.raise_for_status()
            return str(response.json()["choices"][0]["message"]["content"]).strip()
        except (httpx.HTTPError, KeyError, IndexError, TypeError):
            # Do not expose provider errors or any part of a credential to users.
            return "Không thể gọi chatbot lúc này. Dưới đây là các đoạn nguồn phù hợp nhất."

    def close(self) -> None:
        self.client.close()
