"""추상 LLM 클라이언트 인터페이스."""

from abc import ABC, abstractmethod


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
