"""OpenAI LLM 클라이언트 (Codex CLI 호환)."""

import os

try:
    from openai import OpenAI
except ImportError as e:
    raise ImportError("openai 패키지가 설치되지 않았습니다. `pip install openai`를 실행하세요.") from e

from contract_review.llm.base import LLMClient

DEFAULT_MODEL = "gpt-4o"
MAX_TOKENS = 4096


class OpenAIClient(LLMClient):
    """OpenAI API 클라이언트."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.model = model
        self._client = OpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url,  # Codex CLI 등 호환 엔드포인트 지원
        )

    def complete(self, prompt: str, system: str = "") -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content or ""
