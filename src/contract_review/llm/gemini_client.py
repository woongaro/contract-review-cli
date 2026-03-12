"""Gemini CLI를 subprocess로 호출하는 클라이언트."""

from contract_review.llm.base import LLMClient, run_cli_completion


class GeminiClient(LLMClient):
    """Gemini CLI(`gemini`) 기반 클라이언트. API 키 불필요."""

    def __init__(self, cli: str = "gemini") -> None:
        self._cli = cli

    def complete(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        return run_cli_completion([self._cli], full_prompt, "gemini")
