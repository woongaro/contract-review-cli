"""Anthropic Claude LLM 클라이언트."""

import os

try:
    import anthropic
except ImportError as e:
    raise ImportError("anthropic 패키지가 설치되지 않았습니다. `pip install anthropic`를 실행하세요.") from e

from contract_review.llm.base import LLMClient

DEFAULT_MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 4096


class ClaudeClient(LLMClient):
    """Anthropic Claude API 클라이언트."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
        )

    def complete(self, prompt: str, system: str = "") -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        message = self._client.messages.create(**kwargs)
        return message.content[0].text
