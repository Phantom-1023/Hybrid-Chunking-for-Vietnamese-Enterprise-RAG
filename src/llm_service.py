"""
LLM Service Module
Supports DeepSeek as the primary provider, plus OpenAI and Ollama fallbacks.
"""

from typing import Optional, List, Dict
import requests

from src.utils import setup_logger, retry_on_exception
from config.settings import settings

logger = setup_logger(__name__)


class LLMService:
    """Generate grounded answers with the configured LLM provider."""

    def __init__(self):
        self.logger = logger
        self.provider = settings.llm_provider
        self.ollama_url = f"{settings.ollama_base_url}/api/generate"

        self.deepseek_configured = bool(settings.deepseek_api_key)
        self.openai_configured = bool(settings.openai_api_key)

        if self.provider not in {"deepseek", "openai", "ollama"}:
            self.logger.warning(f"Unknown LLM_PROVIDER='{self.provider}', falling back to deepseek")
            self.provider = "deepseek"

    @retry_on_exception(max_retries=2, delay=2)
    def generate_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        if self.provider == "deepseek":
            if self.deepseek_configured:
                return self._generate_deepseek(prompt, system_prompt)
            return self._missing_deepseek_key_message()

        if self.provider == "openai":
            if self.openai_configured:
                return self._generate_openai(prompt, system_prompt)
            return "OPENAI_API_KEY chưa được cấu hình trong file .env."

        return self._generate_ollama(prompt, system_prompt)

    def _generate_deepseek(self, prompt: str, system_prompt: Optional[str]) -> str:
        messages = self._build_messages(prompt, system_prompt)
        response = requests.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.deepseek_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 1200,
            },
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

    def _generate_openai(self, prompt: str, system_prompt: Optional[str]) -> str:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=self._build_messages(prompt, system_prompt),
            temperature=0.2,
        )
        return response.choices[0].message.content

    def _generate_ollama(self, prompt: str, system_prompt: Optional[str]) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
        try:
            response = requests.post(
                self.ollama_url,
                json={
                    "model": settings.llm_model_name,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {"temperature": 0.2},
                },
                timeout=90,
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            self.logger.error(f"Ollama error: {e}")
            return f"Không thể kết nối Ollama tại {settings.ollama_base_url}. Chi tiết: {e}"

    def _build_messages(self, prompt: str, system_prompt: Optional[str]) -> List[Dict[str, str]]:
        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    def _missing_deepseek_key_message(self) -> str:
        return (
            "DeepSeek chưa được cấu hình. Hãy tạo file .env từ .env.example và điền:\n\n"
            "LLM_PROVIDER=deepseek\n"
            "DEEPSEEK_API_KEY=sk-...\n"
            "DEEPSEEK_MODEL=deepseek-v4-pro\n"
            "DEEPSEEK_BASE_URL=https://api.deepseek.com/v1"
        )

    def get_provider_status(self) -> Dict[str, str]:
        return {
            "provider": self.provider,
            "deepseek": "configured" if self.deepseek_configured else "missing_api_key",
            "openai": "configured" if self.openai_configured else "missing_api_key",
        }
