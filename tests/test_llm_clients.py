"""LLM CLI 클라이언트 테스트."""

from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from contract_review.llm.claude_client import ClaudeClient
from contract_review.llm.gemini_client import GeminiClient
from contract_review.llm.openai_client import OpenAIClient


@pytest.mark.parametrize(
    ("client", "expected_command", "backend_name"),
    [
        (ClaudeClient(cli="claude"), ["claude", "--print"], "claude"),
        (GeminiClient(cli="gemini"), ["gemini"], "gemini"),
        (OpenAIClient(cli="codex"), ["codex", "--quiet"], "codex"),
    ],
)
def test_clients_pass_prompt_via_stdin(client, expected_command, backend_name):
    with patch("contract_review.llm.base.subprocess.run") as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=expected_command,
            returncode=0,
            stdout="ok",
            stderr="",
        )

        result = client.complete("PROMPT", system="SYSTEM")

    assert result == "ok"
    mock_run.assert_called_once()
    assert mock_run.call_args.args[0] == expected_command
    assert mock_run.call_args.kwargs["input"] == "SYSTEM\n\nPROMPT"
    assert mock_run.call_args.kwargs["timeout"] > 0


def test_client_missing_binary_raises_runtime_error():
    with patch("contract_review.llm.base.subprocess.run", side_effect=FileNotFoundError):
        with pytest.raises(RuntimeError, match="claude CLI를 찾을 수 없습니다"):
            ClaudeClient(cli="claude").complete("PROMPT")
