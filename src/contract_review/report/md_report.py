"""Markdown 형식 리포트 저장."""

from pathlib import Path

from contract_review.models.diff import DiffReport
from contract_review.models.review import ReviewReport

_RISK_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
    "critical": "🚨",
}

_SEVERITY_KO = {
    "low": "낮음",
    "medium": "보통",
    "high": "높음",
    "critical": "심각",
}

_ISSUE_TYPE_KO = {
    "unfair_term": "불공정 조항",
    "missing_clause": "누락 조항",
    "illegal_term": "위법 조항",
    "ambiguous_term": "모호한 표현",
    "one_sided_term": "일방적 조항",
}

_CHANGE_TYPE_KO = {
    "added_clause": "조항 추가",
    "deleted_clause": "조항 삭제",
    "substantive_change": "실질적 변경",
    "cosmetic_change": "표현 변경",
    "numeric_change": "수치 변경",
    "renumbered_clause": "번호 변경",
}

_CONTRACT_TYPE_KO = {
    "employment": "근로계약",
    "service": "용역/도급",
    "lease": "임대차",
    "nda": "비밀유지",
    "general": "일반 계약",
}


def save_markdown(report: ReviewReport | DiffReport, output_path: str | Path) -> Path:
    """리포트를 Markdown 파일로 저장합니다."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if isinstance(report, ReviewReport):
        content = _review_to_markdown(report)
    else:
        content = _diff_to_markdown(report)

    output_path.write_text(content, encoding="utf-8")
    return output_path


def _review_to_markdown(report: ReviewReport) -> str:
    risk_icon = _RISK_EMOJI.get(report.overall_risk, "⚪")
    contract_ko = _CONTRACT_TYPE_KO.get(report.contract_type.value, report.contract_type.value)

    lines = [
        "# 계약서 검토 리포트",
        "",
        "## 개요",
        "",
        f"| 항목 | 내용 |",
        f"|------|------|",
        f"| 파일 | `{report.source_file}` |",
        f"| 계약 유형 | {contract_ko} |",
        f"| 전체 조항 수 | {report.total_clauses}개 |",
        f"| 종합 위험도 | {risk_icon} {_SEVERITY_KO.get(report.overall_risk, report.overall_risk)} |",
        f"| 발견된 문제 | {len(report.issues)}건 |",
        "",
        "## 검토 요약",
        "",
        report.summary,
        "",
    ]

    if report.issues:
        lines += ["## 발견된 문제", ""]
        critical = report.critical_issues
        high = report.high_issues
        if critical:
            lines += [f"> ⚠️ **심각(critical) 문제 {len(critical)}건** 즉시 검토 필요", ""]
        if high:
            lines += [f"> ⚡ **높음(high) 문제 {len(high)}건** 검토 권장", ""]

        for i, issue in enumerate(report.issues, 1):
            severity_icon = _RISK_EMOJI.get(issue.severity, "⚪")
            issue_type_ko = _ISSUE_TYPE_KO.get(issue.issue_type, issue.issue_type)
            lines += [
                f"### {i}. [{issue.clause_id}] {issue_type_ko}",
                "",
                f"- **심각도**: {severity_icon} {_SEVERITY_KO.get(issue.severity, issue.severity)}",
                f"- **유형**: {issue_type_ko}",
            ]
            if issue.legal_basis:
                lines.append(f"- **법적 근거**: {issue.legal_basis}")
            lines += [
                "",
                f"**문제 설명**: {issue.description}",
                "",
            ]
            if issue.suggestion:
                lines += [
                    f"**개선 제안**: {issue.suggestion}",
                    "",
                ]
    else:
        lines += ["## 검토 결과", "", "✅ 발견된 문제가 없습니다.", ""]

    lines += [
        "---",
        "",
        "*이 리포트는 AI가 생성한 참고 자료입니다. 실제 법률 문제는 변호사와 상담하십시오.*",
    ]
    return "\n".join(lines)


def _diff_to_markdown(report: DiffReport) -> str:
    lines = [
        "# 계약서 비교(Diff) 리포트",
        "",
        "## 개요",
        "",
        f"| 항목 | 내용 |",
        f"|------|------|",
        f"| 이전 버전 | `{report.old_file}` |",
        f"| 새 버전 | `{report.new_file}` |",
        f"| 전체 변경 수 | {len(report.items)}건 |",
        f"| 고위험 변경 | {len(report.high_risk_items)}건 |",
        "",
        "## 변경 요약",
        "",
        report.summary,
        "",
        "## 변경 상세",
        "",
    ]

    for i, item in enumerate(report.items, 1):
        risk_icon = _RISK_EMOJI.get(item.risk_level, "⚪")
        change_ko = _CHANGE_TYPE_KO.get(item.change_type, item.change_type)
        clause_label = item.new_clause_id or item.old_clause_id or "?"

        lines += [
            f"### {i}. [{clause_label}] {change_ko}",
            "",
            f"- **변경 유형**: {change_ko}",
            f"- **위험도**: {risk_icon} {item.risk_level}",
            f"- **요약**: {item.summary}",
            "",
            f"**판단 근거**: {item.rationale}",
            "",
        ]
        if item.old_text:
            lines += [
                "**이전:**",
                f"```",
                item.old_text,
                "```",
                "",
            ]
        if item.new_text:
            lines += [
                "**변경:**",
                "```",
                item.new_text,
                "```",
                "",
            ]

    lines += [
        "---",
        "",
        "*이 리포트는 AI가 생성한 참고 자료입니다. 실제 법률 문제는 변호사와 상담하십시오.*",
    ]
    return "\n".join(lines)
