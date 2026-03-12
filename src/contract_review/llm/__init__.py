from .base import LLMClient
from .claude_client import ClaudeClient
from .gemini_client import GeminiClient
from .openai_client import OpenAIClient


def get_client(backend: str = "claude") -> LLMClient:
    """백엔드 이름으로 LLMClient 인스턴스를 반환합니다."""
    clients = {
        "claude": ClaudeClient,
        "gemini": GeminiClient,
        "openai": OpenAIClient,
    }
    if backend not in clients:
        raise ValueError(f"지원하지 않는 LLM 백엔드: '{backend}'. 선택 가능: {list(clients.keys())}")
    return clients[backend]()


__all__ = ["LLMClient", "ClaudeClient", "GeminiClient", "OpenAIClient", "get_client"]
