"""Google Gemini LLM 클라이언트."""

import os

try:
    from google import genai
    from google.genai import types as genai_types
    _USE_NEW_SDK = True
except ImportError:
    try:
        import google.generativeai as genai  # type: ignore[no-redef]
        _USE_NEW_SDK = False
    except ImportError as e:
        raise ImportError(
            "google-genai 패키지가 설치되지 않았습니다. `pip install google-genai`를 실행하세요."
        ) from e

from contract_review.llm.base import LLMClient

DEFAULT_MODEL = "gemini-1.5-pro"


class GeminiClient(LLMClient):
    """Google Gemini API 클라이언트."""

    def __init__(self, model: str = DEFAULT_MODEL, api_key: str | None = None) -> None:
        self.model = model
        self._api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self._use_new_sdk = _USE_NEW_SDK

        if self._use_new_sdk:
            self._client = genai.Client(api_key=self._api_key)
        else:
            genai.configure(api_key=self._api_key)  # type: ignore[attr-defined]
            self._legacy_model = genai.GenerativeModel(model)  # type: ignore[attr-defined]

    def complete(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt

        if self._use_new_sdk:
            response = self._client.models.generate_content(
                model=self.model,
                contents=full_prompt,
            )
            return response.text or ""
        else:
            response = self._legacy_model.generate_content(full_prompt)  # type: ignore[attr-defined]
            return response.text
