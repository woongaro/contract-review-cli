"""계약서 비교(Diff) 모델."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DiffItem(BaseModel):
    """두 계약서 간 단일 변경 항목."""

    old_clause_id: Optional[str] = Field(None, description="이전 버전 조항 ID")
    new_clause_id: Optional[str] = Field(None, description="새 버전 조항 ID")
    change_type: Literal[
        "added_clause",
        "deleted_clause",
        "substantive_change",
        "cosmetic_change",
        "numeric_change",
        "renumbered_clause",
    ] = Field(..., description="변경 유형")
    summary: str = Field(..., description="변경 내용 요약")
    old_text: Optional[str] = Field(None, description="이전 조항 원문")
    new_text: Optional[str] = Field(None, description="변경된 조항 원문")
    risk_level: Literal["low", "medium", "high"] = Field(..., description="위험도")
    rationale: str = Field(..., description="위험도 판단 근거 및 한국 법령 관련성")


class DiffReport(BaseModel):
    """두 계약서 전체 비교 리포트."""

    old_file: str = Field(..., description="이전 버전 파일 경로")
    new_file: str = Field(..., description="새 버전 파일 경로")
    items: List[DiffItem] = Field(default_factory=list, description="변경 항목 목록")
    summary: str = Field(..., description="전체 변경 요약")

    @property
    def high_risk_items(self) -> List[DiffItem]:
        return [item for item in self.items if item.risk_level == "high"]

    @property
    def added_clauses(self) -> List[DiffItem]:
        return [item for item in self.items if item.change_type == "added_clause"]

    @property
    def deleted_clauses(self) -> List[DiffItem]:
        return [item for item in self.items if item.change_type == "deleted_clause"]
