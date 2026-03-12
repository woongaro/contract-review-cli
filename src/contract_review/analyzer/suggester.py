"""특정 조항 개선 제안 분석기."""

import json
from typing import Any

from contract_review.analyzer.reviewer import _build_safe_parse_error_message, _extract_json
from contract_review.llm.base import LLMClient
from contract_review.models.clause import Clause, ClauseCollection
from contract_review.prompts.suggest_prompts import get_suggest_system_prompt
from contract_review.redaction import redact_text


class Suggester:
    """계약서 조항 개선 제안을 생성합니다."""

    def __init__(self, llm: LLMClient, redact_sensitive: bool = False) -> None:
        self._llm = llm
        self._redact_sensitive = redact_sensitive

    def suggest(
        self,
        collection: ClauseCollection,
        clause_id: str,
    ) -> dict[str, Any]:
        """특정 조항에 대한 개선 제안을 반환합니다."""
        clause = collection.get_clause(clause_id)
        if clause is None:
            raise ValueError(f"조항 '{clause_id}'을(를) 찾을 수 없습니다.")

        return self._suggest_clause(clause, collection.contract_type)

    def suggest_all_issues(
        self,
        collection: ClauseCollection,
        clause_ids: list[str],
    ) -> list[dict[str, Any]]:
        """여러 조항에 대한 개선 제안을 일괄 반환합니다."""
        results = []
        for clause_id in clause_ids:
            try:
                result = self.suggest(collection, clause_id)
                results.append(result)
            except ValueError:
                continue
        return results

    def _suggest_clause(
        self,
        clause: Clause,
        contract_type: str | None,
    ) -> dict[str, Any]:
        contract_context = f"계약서 유형: {contract_type}\n" if contract_type else ""
        heading_text = clause.heading or ""
        clause_text = clause.text
        if self._redact_sensitive:
            heading_text = redact_text(heading_text)
            clause_text = redact_text(clause_text)
        prompt = (
            f"{contract_context}"
            f"다음 조항을 한국 법령에 맞게 개선하는 구체적인 대안 문구를 제안하십시오:\n\n"
            f"[{clause.clause_id}]"
            f"{' (' + heading_text + ')' if heading_text else ''}\n"
            f"{clause_text}"
        )
        response = self._llm.complete(prompt=prompt, system=get_suggest_system_prompt())
        return self._parse_response(response, clause)

    def _parse_response(self, response: str, clause: Clause) -> dict[str, Any]:
        try:
            text = _extract_json(response)
            return json.loads(text)
        except (json.JSONDecodeError, ValueError) as exc:
            return {
                "clause_id": clause.clause_id,
                "original_text": clause.text,
                "issues": [],
                "legal_basis": [],
                "suggested_text": "",
                "explanation": _build_safe_parse_error_message(exc),
            }
