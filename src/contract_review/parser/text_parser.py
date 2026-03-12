"""일반 텍스트 파일에서 계약 조항을 파싱합니다."""

from pathlib import Path

from contract_review.models.clause import ClauseCollection
from contract_review.parser.pdf_parser import PDFParser


class TextParser:
    """텍스트 파일 파서 (PDF 파서의 텍스트 분할 로직 재사용)."""

    def parse(self, file_path: str | Path) -> ClauseCollection:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

        text = file_path.read_text(encoding="utf-8")

        # PDF 파서의 세그멘테이션 로직 재사용
        _pdf_parser = PDFParser()
        clauses = _pdf_parser._segment_clauses(text)

        return ClauseCollection(
            source_file=str(file_path),
            clauses=clauses,
        )
