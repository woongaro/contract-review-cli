"""파서 단위 테스트 (PDF 없이 텍스트 기반)."""

import tempfile
from pathlib import Path

import pytest

from contract_review.parser.pdf_parser import PDFParser, _extract_defined_terms
from contract_review.parser.text_parser import TextParser


SAMPLE_CONTRACT = """제1조 (목적)
이 계약은 "갑"과 "을" 사이의 근로 관계를 규정하는 것을 목적으로 한다.

제2조 (근로 장소 및 업무)
1. 근로 장소: 서울특별시 강남구 소재 회사 사무실
2. 담당 업무: 소프트웨어 개발 및 관련 업무

제3조 (근로 시간)
소정근로시간은 1일 8시간, 주 40시간으로 하며, 시업시각은 09:00, 종업시각은 18:00로 한다.

제4조 (임금)
월 기본급은 금 3,000,000원으로 하며, 매월 말일에 지급한다.

제5조 (비밀유지)
을은 재직 중 및 퇴직 후 2년간 회사의 "영업비밀"을 외부에 누설하지 아니한다.
"""


class TestTextParser:
    def test_parse_sample_contract(self, tmp_path):
        contract_file = tmp_path / "contract.txt"
        contract_file.write_text(SAMPLE_CONTRACT, encoding="utf-8")

        parser = TextParser()
        collection = parser.parse(contract_file)

        assert collection.source_file == str(contract_file)
        assert collection.total_clauses >= 3  # 최소 3개 조항 기대

    def test_clause_ids_detected(self, tmp_path):
        contract_file = tmp_path / "contract.txt"
        contract_file.write_text(SAMPLE_CONTRACT, encoding="utf-8")

        parser = TextParser()
        collection = parser.parse(contract_file)

        clause_ids = [c.clause_id for c in collection.clauses]
        # 제1조, 제2조 등이 포함되어야 함
        assert any("제1조" in cid or "1조" in cid for cid in clause_ids)

    def test_file_not_found(self):
        parser = TextParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/path/contract.txt")

    def test_empty_file(self, tmp_path):
        contract_file = tmp_path / "empty.txt"
        contract_file.write_text("", encoding="utf-8")

        parser = TextParser()
        collection = parser.parse(contract_file)
        assert collection.total_clauses == 0

    def test_cp949_text_file_supported(self, tmp_path):
        contract_file = tmp_path / "contract-cp949.txt"
        contract_file.write_text(SAMPLE_CONTRACT, encoding="cp949")

        parser = TextParser()
        collection = parser.parse(contract_file)

        assert collection.total_clauses >= 3


class TestDefinedTermExtraction:
    def test_korean_quotes(self):
        text = '"갑"과 "을"이 계약을 체결한다'
        terms = _extract_defined_terms(text)
        assert "갑" in terms
        assert "을" in terms

    def test_no_terms(self):
        text = "일반적인 계약 내용입니다."
        terms = _extract_defined_terms(text)
        assert terms == []


class TestPDFParserTextSegmentation:
    """PDF 파서의 텍스트 분할 로직만 테스트 (pdfplumber 없이)."""

    def test_segment_clauses(self):
        parser = PDFParser()
        clauses = parser._segment_clauses(SAMPLE_CONTRACT)
        assert len(clauses) >= 3

    def test_heading_extraction(self):
        parser = PDFParser()
        text = "제1조 (목적)\n이 계약의 목적은..."
        clauses = parser._segment_clauses(text)
        assert len(clauses) >= 1
        first = clauses[0]
        assert first.clause_id == "제1조"
        assert first.heading == "목적"

    def test_nested_numbered_lines_stay_in_same_article(self):
        parser = PDFParser()
        clauses = parser._segment_clauses(SAMPLE_CONTRACT)

        assert len(clauses) == 5
        second_clause = clauses[1]
        assert second_clause.clause_id == "제2조"
        assert "1. 근로 장소" in second_clause.text
        assert "2. 담당 업무" in second_clause.text

    def test_chapter_section_path_is_preserved(self):
        parser = PDFParser()
        text = """제1장 총칙
제1조(목적)
내용1
제2장 기타
제2조(기타)
내용2
"""

        clauses = parser._segment_clauses(text)

        assert clauses[0].section_path == ["제1장 총칙"]
        assert clauses[1].section_path == ["제2장 기타"]
