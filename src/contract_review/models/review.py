"""계약서 검토 결과 모델."""

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class ContractType(str, Enum):
    EMPLOYMENT = "employment"  # 근로계약
    SERVICE = "service"        # 용역/도급
    LEASE = "lease"            # 임대차
    NDA = "nda"                # 비밀유지
    GENERAL = "general"        # 기타


class ReviewIssue(BaseModel):
    """계약서 검토 중 발견된 단일 문제."""

    clause_id: str = Field(..., description="문제가 발견된 조항 ID")
    issue_type: Literal[
        "unfair_term",
        "missing_clause",
        "illegal_term",
        "ambiguous_term",
        "one_sided_term",
    ] = Field(..., description="문제 유형")
    severity: Literal["low", "medium", "high", "critical"] = Field(..., description="심각도")
    description: str = Field(..., description="문제 상세 설명")
    legal_basis: Optional[str] = Field(None, description="관련 한국 법령 (예: '근로기준법 제17조')")
    suggestion: Optional[str] = Field(None, description="개선 제안")


class ReviewReport(BaseModel):
    """계약서 전체 검토 결과."""

    source_file: str = Field(..., description="검토 대상 파일 경로")
    contract_type: ContractType = Field(..., description="계약서 유형")
    total_clauses: int = Field(..., description="전체 조항 수")
    issues: List[ReviewIssue] = Field(default_factory=list, description="발견된 문제 목록")
    overall_risk: Literal["low", "medium", "high", "critical"] = Field(..., description="종합 위험도")
    summary: str = Field(..., description="검토 결과 종합 요약")

    @property
    def critical_issues(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == "critical"]

    @property
    def high_issues(self) -> List[ReviewIssue]:
        return [i for i in self.issues if i.severity == "high"]
