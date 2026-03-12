"""추상 LLM 클라이언트 인터페이스."""

from abc import ABC, abstractmethod
from collections.abc import Sequence
import subprocess


CLI_TIMEOUT_SECONDS = 180


class LLMClient(ABC):
    """모든 LLM 백엔드의 기반 추상 클래스."""

    @abstractmethod
    def complete(self, prompt: str, system: str = "") -> str:
        """LLM에 프롬프트를 전송하고 응답 텍스트를 반환합니다.

        Args:
            prompt: 사용자 메시지
            system: 시스템 프롬프트 (선택)

        Returns:
            LLM 응답 텍스트
        """
        ...


def run_cli_completion(command: Sequence[str], prompt: str, backend_name: str) -> str:
    """LLM CLI를 실행하고 stdin으로 프롬프트를 전달합니다."""
    try:
        result = subprocess.run(
            list(command),
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CLI_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(f"{backend_name} CLI를 찾을 수 없습니다: {command[0]}") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"{backend_name} CLI 응답 시간이 초과되었습니다.") from exc

    if result.returncode != 0:
        raise RuntimeError(
            f"{backend_name} CLI 오류 (exit {result.returncode}):\n{result.stderr}"
        )

    return result.stdout.strip()
