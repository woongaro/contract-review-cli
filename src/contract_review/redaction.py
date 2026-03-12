"""LLM 전송 전 민감정보 마스킹 유틸리티."""

from __future__ import annotations

import re
from pathlib import Path


REDACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (
        re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
        "[REDACTED_EMAIL]",
    ),
    (
        re.compile(r"(?<!\d)(?:\+82[- ]?)?0\d{1,2}-?\d{3,4}-?\d{4}(?!\d)"),
        "[REDACTED_PHONE]",
    ),
    (
        re.compile(r"\b\d{6}-?[1-8]\d{6}\b"),
        "[REDACTED_ID_NUMBER]",
    ),
    (
        re.compile(r"\b\d{3}-\d{2}-\d{5}\b"),
        "[REDACTED_BIZ_REG_NO]",
    ),
    (
        re.compile(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b"),
        "[REDACTED_UUID]",
    ),
]


def redact_text(text: str) -> str:
    """이메일·전화번호·등록번호·UUID 등 직접 식별자를 단순 마스킹합니다."""
    redacted = text
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_file_reference(path: str) -> str:
    """프롬프트에서 파일 경로를 직접 노출하지 않도록 대체합니다."""
    suffix = Path(path).suffix
    return f"[REDACTED_FILE{suffix}]" if suffix else "[REDACTED_FILE]"
