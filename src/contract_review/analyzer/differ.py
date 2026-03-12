"""두 계약서 버전 비교(Diff) 분석기."""

import json

from contract_review.analyzer.reviewer import _extract_json
from contract_review.llm.base import LLMClient
from contract_review.models.clause import ClauseCollection
from contract_review.models.diff import DiffItem, DiffReport
from contract_review.prompts.diff_prompts import get_diff_system_prompt


class Differ:
    """두 계약서를 비교하여 변경 사항과 위험도를 분석합니다."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

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
        parts = [f"## {label}: {collection.source_file}"]
        for clause in collection.clauses:
            heading = f" ({clause.heading})" if clause.heading else ""
            parts.append(f"[{clause.clause_id}{heading}]\n{clause.text}")
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
                summary=f"[파싱 오류: {exc}]\n\nLLM 원본 응답:\n{response}",
            )
