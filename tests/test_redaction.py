"""민감정보 마스킹 유틸리티 테스트."""

from contract_review.redaction import redact_file_reference, redact_text


def test_redact_text_masks_supported_identifiers():
    text = (
        "담당자 alice@example.com, 연락처 010-1234-5678, "
        "주민등록번호 900101-1234567, 사업자등록번호 123-45-67890, "
        "DocuSign 550e8400-e29b-41d4-a716-446655440000"
    )

    redacted = redact_text(text)

    assert "alice@example.com" not in redacted
    assert "010-1234-5678" not in redacted
    assert "900101-1234567" not in redacted
    assert "123-45-67890" not in redacted
    assert "550e8400-e29b-41d4-a716-446655440000" not in redacted
    assert "[REDACTED_EMAIL]" in redacted
    assert "[REDACTED_PHONE]" in redacted
    assert "[REDACTED_ID_NUMBER]" in redacted
    assert "[REDACTED_BIZ_REG_NO]" in redacted
    assert "[REDACTED_UUID]" in redacted


def test_redact_file_reference_preserves_only_suffix():
    assert redact_file_reference(r"C:\secret\client-contract.pdf") == "[REDACTED_FILE.pdf]"
    assert redact_file_reference("contract") == "[REDACTED_FILE]"
