"""단일 계약서 검토 분석기."""

import json

from contract_review.analyzer.type_detector import TypeDetector
from contract_review.llm.base import LLMClient
from contract_review.models.clause import ClauseCollection
from contract_review.models.review import ContractType, ReviewIssue, ReviewReport
from contract_review.prompts.review_prompts import get_review_system_prompt
from contract_review.redaction import redact_text


def _build_safe_parse_error_message(exc: Exception) -> str:
    """민감정보 재노출을 피하는 LLM 파싱 오류 메시지."""
    return (
        f"[파싱 오류: {exc}]\n\n"
        "LLM 응답을 JSON으로 해석하지 못했습니다. "
        "민감정보 보호를 위해 원본 응답은 출력하지 않았습니다."
    )

class Reviewer:
    """계약서를 한국 법령 기준으로 검토합니다."""

    def __init__(self, llm: LLMClient, redact_sensitive: bool = False) -> None:
        self._llm = llm
        self._redact_sensitive = redact_sensitive
        self._detector = TypeDetector(llm, redact_sensitive=redact_sensitive)

    def review(
        self,
        collection: ClauseCollection,
        contract_type: ContractType | None = None,
    ) -> ReviewReport:
        """ClauseCollection을 검토하여 ReviewReport를 반환합니다."""
        # 1. 계약 유형 감지
        detected_type = contract_type or self._detector.detect(collection)

        # 2. 시스템 프롬프트 선택
        system_prompt = get_review_system_prompt(detected_type)

        # 3. 계약서 텍스트 구성
        contract_text = self._build_contract_text(collection)

        # 4. LLM 호출
        response = self._llm.complete(
            prompt=f"다음 계약서를 검토하여 문제점을 찾아주십시오:\n\n{contract_text}",
            system=system_prompt,
        )

        # 5. 응답 파싱
        return self._parse_response(response, collection, detected_type)

    def _build_contract_text(self, collection: ClauseCollection) -> str:
        parts = []
        for clause in collection.clauses:
            heading_text = clause.heading or ""
            clause_text = clause.text
            if self._redact_sensitive:
                heading_text = redact_text(heading_text)
                clause_text = redact_text(clause_text)
            heading = f" ({heading_text})" if heading_text else ""
            parts.append(f"[{clause.clause_id}{heading}]\n{clause_text}")
        return "\n\n".join(parts)

    def _parse_response(
        self,
        response: str,
        collection: ClauseCollection,
        detected_type: ContractType,
    ) -> ReviewReport:
        try:
            text = _extract_json(response)
            data = json.loads(text)

            issues = [ReviewIssue(**item) for item in data.get("issues", [])]

            return ReviewReport(
                source_file=collection.source_file,
                contract_type=ContractType(data.get("contract_type", detected_type.value)),
                total_clauses=collection.total_clauses,
                issues=issues,
                overall_risk=data.get("overall_risk", "medium"),
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            # 파싱 실패 시 빈 리포트 반환 (원본 응답은 재노출하지 않음)
            return ReviewReport(
                source_file=collection.source_file,
                contract_type=detected_type,
                total_clauses=collection.total_clauses,
                issues=[],
                overall_risk="medium",
                summary=_build_safe_parse_error_message(exc),
            )


def _extract_json(text: str) -> str:
    """응답 텍스트에서 JSON 부분만 추출합니다."""
    text = text.strip()
    if "```" in text:
        parts = text.split("```")
        first_block = None
        for part in parts[1::2]:
            if part.startswith("json"):
                return part[4:].strip()
            if first_block is None:
                first_block = part.strip()
        if first_block is not None:
            return first_block
    # { } 로 감싸진 부분 추출
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        return text[start:end]
    return text
