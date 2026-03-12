"""LLM을 이용한 계약서 유형 자동 감지."""

import json

from contract_review.llm.base import LLMClient
from contract_review.models.clause import ClauseCollection
from contract_review.models.review import ContractType
from contract_review.redaction import redact_text

DETECT_SYSTEM = """당신은 한국 법률 전문가 AI입니다.
주어진 계약서 내용을 분석하여 계약서 유형을 분류하십시오.

반드시 아래 JSON 형식으로만 응답하십시오:
{"contract_type": "employment|service|lease|nda|general", "reason": "분류 이유"}

- employment: 근로계약서 (고용주-근로자)
- service: 용역/도급 계약서 (서비스 제공·수행)
- lease: 임대차 계약서 (부동산 임대)
- nda: 비밀유지계약서 (기밀정보 보호)
- general: 기타 일반 계약"""


class TypeDetector:
    """계약서 유형을 LLM으로 자동 감지합니다."""

    def __init__(self, llm: LLMClient, redact_sensitive: bool = False) -> None:
        self._llm = llm
        self._redact_sensitive = redact_sensitive

    def detect(self, collection: ClauseCollection) -> ContractType:
        """계약서 유형을 감지하여 ContractType을 반환합니다."""
        # 첫 5개 조항 + 전체 텍스트 요약을 활용
        sample_text = self._build_sample(collection)
        response = self._llm.complete(
            prompt=f"다음 계약서를 분류하십시오:\n\n{sample_text}",
            system=DETECT_SYSTEM,
        )
        return self._parse_response(response)

    def _build_sample(self, collection: ClauseCollection) -> str:
        sample_clauses = collection.clauses[:5]
        parts = []
        for clause in sample_clauses:
            heading = clause.heading or ""
            text = clause.text
            if self._redact_sensitive:
                heading = redact_text(heading)
                text = redact_text(text)
            parts.append(f"[{clause.clause_id}] {heading}\n{text}")
        return "\n\n".join(parts)

    def _parse_response(self, response: str) -> ContractType:
        try:
            # JSON 블록 추출
            text = response.strip()
            if "```" in text:
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            data = json.loads(text.strip())
            return ContractType(data.get("contract_type", "general"))
        except (json.JSONDecodeError, ValueError, KeyError):
            return ContractType.GENERAL
