"""두 계약서 버전 비교(Diff) 분석기."""

import json

from contract_review.analyzer.reviewer import _build_safe_parse_error_message, _extract_json
from contract_review.llm.base import LLMClient
from contract_review.models.clause import ClauseCollection
from contract_review.models.diff import DiffItem, DiffReport
from contract_review.prompts.diff_prompts import get_diff_system_prompt
from contract_review.redaction import redact_file_reference, redact_text


class Differ:
    """두 계약서를 비교하여 변경 사항과 위험도를 분석합니다."""

    def __init__(self, llm: LLMClient, redact_sensitive: bool = False) -> None:
        self._llm = llm
        self._redact_sensitive = redact_sensitive

    def diff(
        self,
        old_collection: ClauseCollection,
        new_collection: ClauseCollection,
    ) -> DiffReport:
        """두 ClauseCollection을 비교하여 DiffReport를 반환합니다."""
        old_text = self._build_contract_text(old_collection, "이전 버전")
        new_text = self._build_contract_text(new_collection, "새 버전")

        prompt = (
            f"아래 두 계약서 버전을 비교하여 변경 사항을 분석하십시오.\n\n"
            f"{old_text}\n\n{'='*60}\n\n{new_text}"
        )

        response = self._llm.complete(prompt=prompt, system=get_diff_system_prompt())
        return self._parse_response(response, old_collection.source_file, new_collection.source_file)

    def _build_contract_text(self, collection: ClauseCollection, label: str) -> str:
        file_reference = collection.source_file
        if self._redact_sensitive:
            file_reference = redact_file_reference(collection.source_file)

        parts = [f"## {label}: {file_reference}"]
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
        old_file: str,
        new_file: str,
    ) -> DiffReport:
        try:
            text = _extract_json(response)
            data = json.loads(text)
            items = [DiffItem(**item) for item in data.get("items", [])]
            return DiffReport(
                old_file=old_file,
                new_file=new_file,
                items=items,
                summary=data.get("summary", ""),
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            return DiffReport(
                old_file=old_file,
                new_file=new_file,
                items=[],
                summary=_build_safe_parse_error_message(exc),
            )
