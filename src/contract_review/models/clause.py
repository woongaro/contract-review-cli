"""계약서 조항 모델."""

import re
from typing import List, Optional

from pydantic import BaseModel, Field


ARTICLE_ID_PATTERN = re.compile(r"^제\s*(\d+)\s*조(?:\s*\([^)]+\))?")
PARAGRAPH_ID_PATTERN = re.compile(r"^제\s*(\d+)\s*항")
NUMERIC_ID_PATTERN = re.compile(r"^(\d+)\.")
LETTER_ID_PATTERN = re.compile(r"^([가-힣])\.")


def normalize_clause_id(clause_id: str) -> str:
    """조항 식별자를 표준화합니다."""
    text = " ".join(clause_id.strip().split())

    article_match = ARTICLE_ID_PATTERN.match(text)
    if article_match:
        return f"제{int(article_match.group(1))}조"

    paragraph_match = PARAGRAPH_ID_PATTERN.match(text)
    if paragraph_match:
        return f"제{int(paragraph_match.group(1))}항"

    numeric_match = NUMERIC_ID_PATTERN.match(text)
    if numeric_match:
        return f"{int(numeric_match.group(1))}."

    letter_match = LETTER_ID_PATTERN.match(text)
    if letter_match:
        return f"{letter_match.group(1)}."

    return text


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
        normalized_clause_id = normalize_clause_id(clause_id)
        for clause in self.clauses:
            if clause.clause_id == clause_id:
                return clause
            if normalize_clause_id(clause.clause_id) == normalized_clause_id:
                return clause
        return None
