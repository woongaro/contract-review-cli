"""계약서 조항 모델."""

from typing import List, Optional

from pydantic import BaseModel, Field


class Clause(BaseModel):
    """단일 계약 조항."""

    clause_id: str = Field(..., description="조항 식별자 (예: '제1조', '1.1')")
    heading: Optional[str] = Field(None, description="조항 제목")
    text: str = Field(..., description="조항 전문")
    section_path: List[str] = Field(default_factory=list, description="계층 경로 (예: ['제1장', '제1조'])")
    defined_terms: List[str] = Field(default_factory=list, description="해당 조항에서 정의된 용어")


class ClauseCollection(BaseModel):
    """계약서 전체 조항 집합."""

    source_file: str = Field(..., description="원본 파일 경로")
    contract_type: Optional[str] = Field(None, description="감지된 계약서 유형")
    clauses: List[Clause] = Field(default_factory=list, description="조항 목록")

    @property
    def total_clauses(self) -> int:
        return len(self.clauses)

    def get_clause(self, clause_id: str) -> Optional[Clause]:
        for clause in self.clauses:
            if clause.clause_id == clause_id:
                return clause
        return None
