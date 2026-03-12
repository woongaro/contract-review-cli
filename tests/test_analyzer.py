"""분석기 단위 테스트 (LLM Mock 사용)."""

import json
from unittest.mock import MagicMock

import pytest

from contract_review.analyzer.differ import Differ
from contract_review.analyzer.reviewer import Reviewer
from contract_review.analyzer.suggester import Suggester
from contract_review.analyzer.type_detector import TypeDetector
from contract_review.llm.base import LLMClient
from contract_review.models.clause import Clause, ClauseCollection
from contract_review.models.review import ContractType


def _make_collection(n_clauses: int = 3, source: str = "test.pdf") -> ClauseCollection:
    clauses = [
        Clause(clause_id=f"제{i}조", heading=f"조항{i}", text=f"내용 {i}번째 조항입니다.")
        for i in range(1, n_clauses + 1)
    ]
    return ClauseCollection(source_file=source, clauses=clauses)


def _mock_llm(response: str) -> LLMClient:
    mock = MagicMock(spec=LLMClient)
    mock.complete.return_value = response
    return mock


class TestTypeDetector:
    def test_detect_employment(self):
        response = json.dumps({"contract_type": "employment", "reason": "근로계약서"})
        detector = TypeDetector(_mock_llm(response))
        result = detector.detect(_make_collection())
        assert result == ContractType.EMPLOYMENT

    def test_detect_fallback_on_invalid(self):
        detector = TypeDetector(_mock_llm("invalid json response"))
        result = detector.detect(_make_collection())
        assert result == ContractType.GENERAL

    def test_detect_nda(self):
        response = json.dumps({"contract_type": "nda", "reason": "비밀유지계약"})
        detector = TypeDetector(_mock_llm(response))
        result = detector.detect(_make_collection())
        assert result == ContractType.NDA

    def test_detect_redacts_sensitive_data_in_prompt(self):
        mock_llm = _mock_llm(json.dumps({"contract_type": "general", "reason": "ok"}))
        detector = TypeDetector(mock_llm, redact_sensitive=True)
        collection = ClauseCollection(
            source_file="test.pdf",
            clauses=[
                Clause(
                    clause_id="제1조",
                    heading="담당자 alice@example.com",
                    text="연락처 010-1234-5678 / 주민등록번호 900101-1234567",
                )
            ],
        )

        detector.detect(collection)

        prompt = mock_llm.complete.call_args.kwargs["prompt"]
        assert "alice@example.com" not in prompt
        assert "010-1234-5678" not in prompt
        assert "900101-1234567" not in prompt
        assert "[REDACTED_EMAIL]" in prompt
        assert "[REDACTED_PHONE]" in prompt
        assert "[REDACTED_ID_NUMBER]" in prompt


class TestReviewer:
    def _make_review_response(self, contract_type: str = "employment") -> str:
        return json.dumps({
            "contract_type": contract_type,
            "overall_risk": "medium",
            "summary": "전체적으로 무난한 계약서입니다.",
            "issues": [
                {
                    "clause_id": "제1조",
                    "issue_type": "missing_clause",
                    "severity": "high",
                    "description": "근로기준법 제17조 필수 기재사항 누락",
                    "legal_basis": "근로기준법 제17조",
                    "suggestion": "임금 구성항목을 상세히 기재하십시오.",
                }
            ],
        })

    def test_review_returns_report(self):
        mock_llm = _mock_llm(self._make_review_response())
        reviewer = Reviewer(mock_llm)
        collection = _make_collection()

        report = reviewer.review(collection)

        assert report.source_file == "test.pdf"
        assert report.total_clauses == 3
        assert len(report.issues) == 1
        assert report.overall_risk == "medium"

    def test_review_with_forced_type(self):
        # type_detector가 호출되지 않아야 함
        mock_llm = _mock_llm(self._make_review_response("lease"))
        reviewer = Reviewer(mock_llm)
        collection = _make_collection()

        report = reviewer.review(collection, ContractType.LEASE)
        assert report is not None

    def test_review_handles_parse_error(self):
        mock_llm = _mock_llm("이것은 JSON이 아닙니다.")
        reviewer = Reviewer(mock_llm)
        collection = _make_collection()

        # 파싱 오류 시 빈 issues 리포트 반환
        report = reviewer.review(collection, ContractType.GENERAL)
        assert report.issues == []
        assert "파싱 오류" in report.summary

    def test_build_contract_text_includes_all_clauses(self):
        reviewer = Reviewer(_mock_llm(self._make_review_response()))
        collection = ClauseCollection(
            source_file="many.txt",
            clauses=[Clause(clause_id=f"C{i}", text=f"T{i}") for i in range(1, 32)],
        )

        contract_text = reviewer._build_contract_text(collection)

        assert "C30" in contract_text
        assert "C31" in contract_text

    def test_review_redacts_sensitive_data_in_prompt(self):
        mock_llm = _mock_llm(self._make_review_response())
        reviewer = Reviewer(mock_llm, redact_sensitive=True)
        collection = ClauseCollection(
            source_file="sensitive.pdf",
            clauses=[
                Clause(
                    clause_id="제1조",
                    heading="연락처 alice@example.com",
                    text="담당자 010-1234-5678, 주민등록번호 900101-1234567",
                )
            ],
        )

        reviewer.review(collection, ContractType.GENERAL)

        prompt = mock_llm.complete.call_args.kwargs["prompt"]
        assert "alice@example.com" not in prompt
        assert "010-1234-5678" not in prompt
        assert "900101-1234567" not in prompt
        assert "[REDACTED_EMAIL]" in prompt
        assert "[REDACTED_PHONE]" in prompt
        assert "[REDACTED_ID_NUMBER]" in prompt


class TestDiffer:
    def test_diff_returns_report(self):
        response = json.dumps({
            "summary": "주요 변경 사항: 임금 조항 수정",
            "items": [
                {
                    "old_clause_id": "제4조",
                    "new_clause_id": "제4조",
                    "change_type": "numeric_change",
                    "summary": "월급 300만원 → 350만원",
                    "old_text": "월 기본급 3,000,000원",
                    "new_text": "월 기본급 3,500,000원",
                    "risk_level": "low",
                    "rationale": "임금 인상은 근로자에게 유리한 변경",
                }
            ],
        })
        mock_llm = _mock_llm(response)
        differ = Differ(mock_llm)

        old_col = _make_collection(source="old.pdf")
        new_col = _make_collection(source="new.pdf")

        report = differ.diff(old_col, new_col)
        assert report.old_file == "old.pdf"
        assert report.new_file == "new.pdf"
        assert len(report.items) == 1
        assert report.items[0].change_type == "numeric_change"

    def test_diff_redacts_prompt_text_and_file_reference(self):
        response = json.dumps({"summary": "ok", "items": []})
        mock_llm = _mock_llm(response)
        differ = Differ(mock_llm, redact_sensitive=True)

        old_col = ClauseCollection(
            source_file=r"C:\secret\old-contract.pdf",
            clauses=[Clause(clause_id="제1조", text="담당자 old@example.com")],
        )
        new_col = ClauseCollection(
            source_file=r"C:\secret\new-contract.pdf",
            clauses=[Clause(clause_id="제1조", text="담당자 new@example.com")],
        )

        differ.diff(old_col, new_col)

        prompt = mock_llm.complete.call_args.kwargs["prompt"]
        assert r"C:\secret\old-contract.pdf" not in prompt
        assert r"C:\secret\new-contract.pdf" not in prompt
        assert "old@example.com" not in prompt
        assert "new@example.com" not in prompt
        assert "[REDACTED_FILE.pdf]" in prompt
        assert "[REDACTED_EMAIL]" in prompt


class TestSuggester:
    def test_suggest_returns_result(self):
        response = json.dumps({
            "clause_id": "제3조",
            "original_text": "원본 조항",
            "issues": ["모호한 표현"],
            "legal_basis": ["민법 제105조"],
            "suggested_text": "개선된 조항 문구",
            "explanation": "명확한 표현으로 수정하였습니다.",
        })
        mock_llm = _mock_llm(response)
        suggester = Suggester(mock_llm)
        collection = _make_collection()

        result = suggester.suggest(collection, "제3조")
        assert result["clause_id"] == "제3조"
        assert result["suggested_text"] == "개선된 조항 문구"

    def test_suggest_clause_not_found(self):
        suggester = Suggester(_mock_llm("{}"))
        collection = _make_collection()

        with pytest.raises(ValueError, match="제99조"):
            suggester.suggest(collection, "제99조")


def test_review_parse_error_does_not_echo_llm_response():
    reviewer = Reviewer(_mock_llm("sensitive-review-response"))
    collection = _make_collection()

    report = reviewer.review(collection, ContractType.GENERAL)

    assert report.issues == []
    assert "sensitive-review-response" not in report.summary
    assert "LLM 원본 응답" not in report.summary


def test_diff_parse_error_does_not_echo_llm_response():
    differ = Differ(_mock_llm("sensitive-diff-response"))
    old_collection = _make_collection(source="old.pdf")
    new_collection = _make_collection(source="new.pdf")

    report = differ.diff(old_collection, new_collection)

    assert report.items == []
    assert "sensitive-diff-response" not in report.summary
    assert "LLM 원본 응답" not in report.summary


def test_suggest_parse_error_does_not_echo_llm_response():
    suggester = Suggester(_mock_llm("sensitive-suggest-response"))
    collection = _make_collection()

    result = suggester.suggest(collection, collection.clauses[0].clause_id)

    assert result["clause_id"] == collection.clauses[0].clause_id
    assert "sensitive-suggest-response" not in result["explanation"]
    assert "LLM 원본 응답" not in result["explanation"]
