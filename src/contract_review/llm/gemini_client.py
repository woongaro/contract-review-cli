"""Google Gemini LLM 클라이언트."""

import os

try:
    import google.generativeai as genai
except ImportError as e:
    raise ImportError(
        "google-generativeai 패키지가 설치되지 않았습니다. `pip install google-generativeai`를 실행하세요."
    ) from e

from contract_review.llm.base import LLMClient

DEFAULT_MODEL = "gemini-1.5-pro"


class GeminiClient(LLMClient):
    """Google Gemini API 클라이언트."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        genai.configure(api_key=api_key or os.environ.get("GOOGLE_API_KEY"))
        self._client = genai.GenerativeModel(model)

    def complete(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        response = self._client.generate_content(full_prompt)
        return response.text
