"""PDF 파일에서 계약 조항을 파싱합니다."""

import re
from pathlib import Path
from typing import List, Optional

try:
    import pdfplumber
except ImportError as e:
    raise ImportError("pdfplumber가 설치되지 않았습니다. `pip install pdfplumber`를 실행하세요.") from e

from contract_review.models.clause import Clause, ClauseCollection

# 한국식 조항 번호 패턴
CLAUSE_PATTERNS = [
    re.compile(r"^제\s*(\d+)\s*조\s*(?:\(([^)]+)\))?"),       # 제1조, 제1조(목적)
    re.compile(r"^(\d+)\.\s+([^\n]{1,50})"),                   # 1. 제목
    re.compile(r"^제\s*(\d+)\s*항"),                            # 제1항
    re.compile(r"^([가-힣]+)\.\s+([^\n]{1,50})"),              # 가. 내용
]

DEFINED_TERM_PATTERN = re.compile(r'"([^"]{2,20})"|'([^']{2,20})'|"([^"]{2,20})"')


def _extract_defined_terms(text: str) -> List[str]:
    matches = DEFINED_TERM_PATTERN.findall(text)
    terms = []
    for match in matches:
        term = next((t for t in match if t), None)
        if term:
            terms.append(term)
    return list(set(terms))


def _detect_clause_start(line: str) -> Optional[tuple[str, Optional[str]]]:
    """조항 시작 여부 감지. (clause_id, heading) 또는 None 반환."""
    for pattern in CLAUSE_PATTERNS:
        m = pattern.match(line.strip())
        if m:
            groups = m.groups()
            clause_id = line.strip().split("\n")[0][:30]
            heading = groups[1] if len(groups) > 1 and groups[1] else None
            return clause_id, heading
    return None


class PDFParser:
    """pdfplumber 기반 PDF 계약서 파서."""

    def parse(self, file_path: str | Path) -> ClauseCollection:
        """PDF 파일을 파싱하여 ClauseCollection을 반환합니다."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        text = self._extract_text(file_path)
        clauses = self._segment_clauses(text)

        return ClauseCollection(
            source_file=str(file_path),
            clauses=clauses,
        )

    def _extract_text(self, file_path: Path) -> str:
        """PDF에서 전체 텍스트 추출."""
        pages = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if page_text:
                    pages.append(page_text)
        return "\n".join(pages)

    def _segment_clauses(self, text: str) -> List[Clause]:
        """텍스트를 조항 단위로 분할합니다."""
        lines = text.split("\n")
        clauses: List[Clause] = []
        current_id: Optional[str] = None
        current_heading: Optional[str] = None
        current_lines: List[str] = []
        section_stack: List[str] = []
        clause_counter = 0

        def flush_clause() -> None:
            nonlocal current_id, current_heading, current_lines
            if current_lines and current_id:
                clause_text = "\n".join(current_lines).strip()
                if clause_text:
                    clauses.append(
                        Clause(
                            clause_id=current_id,
                            heading=current_heading,
                            text=clause_text,
                            section_path=list(section_stack),
                            defined_terms=_extract_defined_terms(clause_text),
                        )
                    )
            current_lines = []
            current_id = None
            current_heading = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                if current_lines:
                    current_lines.append("")
                continue

            # 장/편 구분 감지 (section_stack 갱신)
            chapter_match = re.match(r"^제\s*(\d+)\s*[장편절]", stripped)
            if chapter_match:
                section_stack = [stripped[:20]]
                flush_clause()
                continue

            # 조항 시작 감지
            result = _detect_clause_start(stripped)
            if result:
                flush_clause()
                clause_counter += 1
                raw_id, heading = result
                current_id = raw_id if raw_id else str(clause_counter)
                current_heading = heading
                current_lines = [stripped]
            else:
                if current_id is None:
                    # 조항 식별자 없이 시작하는 전문 처리
                    clause_counter += 1
                    current_id = f"전문-{clause_counter}"
                current_lines.append(stripped)

        flush_clause()

        # 조항이 전혀 감지되지 않은 경우 전문을 단일 조항으로 처리
        if not clauses and text.strip():
            clauses.append(
                Clause(
                    clause_id="전문",
                    text=text.strip(),
                    defined_terms=_extract_defined_terms(text),
                )
            )

        return clauses
