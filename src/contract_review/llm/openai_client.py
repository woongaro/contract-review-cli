"""OpenAI Codex CLI를 subprocess로 호출하는 클라이언트."""

import subprocess

from contract_review.llm.base import LLMClient


class OpenAIClient(LLMClient):
    """OpenAI Codex CLI(`codex`) 기반 클라이언트. API 키 불필요."""

    def __init__(self, cli: str = "codex") -> None:
        self._cli = cli

    def complete(self, prompt: str, system: str = "") -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        result = subprocess.run(
            [self._cli, "--quiet", full_prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"codex CLI 오류 (exit {result.returncode}):\n{result.stderr}"
            )
        return result.stdout.strip()
