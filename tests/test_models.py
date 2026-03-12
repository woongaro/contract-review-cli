"""Pydantic 모델 단위 테스트."""

import pytest
from pydantic import ValidationError

from contract_review.models.clause import Clause, ClauseCollection
from contract_review.models.diff import DiffItem, DiffReport
from contract_review.models.review import ContractType, ReviewIssue, ReviewReport


class TestClause:
    def test_basic(self):
        c = Clause(clause_id="제1조", text="목적 조항 내용")
        assert c.clause_id == "제1조"
        assert c.heading is None
        assert c.defined_terms == []

    def test_with_all_fields(self):
        c = Clause(
            clause_id="1.1",
            heading="목적",
            text="이 계약의 목적은...",
            section_path=["제1장"],
            defined_terms=["계약"],
        )
        assert c.heading == "목적"
        assert "계약" in c.defined_terms

    def test_text_required(self):
        with pytest.raises(ValidationError):
            Clause(clause_id="제1조")


class TestClauseCollection:
    def test_total_clauses(self):
        clauses = [Clause(clause_id=f"제{i}조", text=f"내용 {i}") for i in range(1, 4)]
        col = ClauseCollection(source_file="test.pdf", clauses=clauses)
        assert col.total_clauses == 3

    def test_get_clause(self):
        clauses = [Clause(clause_id="제1조", text="내용")]
        col = ClauseCollection(source_file="test.pdf", clauses=clauses)
        assert col.get_clause("제1조") is not None
        assert col.get_clause("제99조") is None

    def test_empty(self):
        col = ClauseCollection(source_file="empty.pdf")
        assert col.total_clauses == 0


class TestDiffItem:
    def test_valid(self):
        item = DiffItem(
            old_clause_id="제1조",
            new_clause_id="제1조",
            change_type="substantive_change",
            summary="임금 변경",
            risk_level="high",
            rationale="근로기준법 위반 소지",
        )
        assert item.risk_level == "high"
        assert item.change_type == "substantive_change"

    def test_invalid_risk_level(self):
        with pytest.raises(ValidationError):
            DiffItem(
                change_type="added_clause",
                summary="테스트",
                risk_level="extreme",  # 유효하지 않은 값
                rationale="테스트",
            )


class TestReviewReport:
    def _make_report(self, **kwargs) -> ReviewReport:
        defaults = dict(
            source_file="test.pdf",
            contract_type=ContractType.EMPLOYMENT,
            total_clauses=10,
            issues=[],
            overall_risk="low",
            summary="이상 없음",
        )
        defaults.update(kwargs)
        return ReviewReport(**defaults)

    def test_basic(self):
        report = self._make_report()
        assert report.contract_type == ContractType.EMPLOYMENT
        assert report.total_clauses == 10

    def test_critical_issues_filter(self):
        issues = [
            ReviewIssue(
                clause_id="제1조",
                issue_type="illegal_term",
                severity="critical",
                description="위법 조항",
            ),
            ReviewIssue(
                clause_id="제2조",
                issue_type="unfair_term",
                severity="low",
                description="경미한 문제",
            ),
        ]
        report = self._make_report(issues=issues, overall_risk="critical")
        assert len(report.critical_issues) == 1
        assert len(report.high_issues) == 0

    def test_contract_type_enum(self):
        assert ContractType.EMPLOYMENT.value == "employment"
        assert ContractType.LEASE.value == "lease"
        assert ContractType("nda") == ContractType.NDA
