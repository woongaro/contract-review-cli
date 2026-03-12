"""계약서 검토 CLI 진입점."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from contract_review.llm import get_client
from contract_review.models.clause import ClauseCollection

load_dotenv()

# Windows: stdout/stderr를 UTF-8로 재설정하여 한글·특수문자 출력 지원
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)  # type: ignore[attr-defined]
    ctypes.windll.kernel32.SetConsoleCP(65001)  # type: ignore[attr-defined]
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

app = typer.Typer(
    name="contract-review",
    help="[KR] 한국 법령 기반 계약서 자동 검토 CLI",
    rich_markup_mode="rich",
)
# legacy_windows=False: Win32 Console API 대신 ANSI 이스케이프 사용 (UTF-8 문자 지원)
console = Console(legacy_windows=False)
err_console = Console(stderr=True, legacy_windows=False)

LLMOption = Annotated[
    str,
    typer.Option("--llm", help="LLM 백엔드 선택 [claude|gemini|openai]", show_default=True),
]
OutputOption = Annotated[
    Optional[Path],
    typer.Option("--output", "-o", help="출력 파일 경로 (.md 또는 .json)"),
]


def _get_parser(file_path: Path):
    """파일 확장자에 따라 파서를 선택합니다."""
    if file_path.suffix.lower() == ".pdf":
        from contract_review.parser.pdf_parser import PDFParser
        return PDFParser()
    else:
        from contract_review.parser.text_parser import TextParser
        return TextParser()


def _load_collection(file_path: Path) -> ClauseCollection:
    parser = _get_parser(file_path)
    return parser.parse(file_path)


@app.command()
def parse(
    file: Annotated[Path, typer.Argument(help="계약서 파일 (PDF 또는 텍스트)")],
    output: OutputOption = None,
) -> None:
    """계약서 파일을 조항 단위로 파싱합니다."""
    if not file.exists():
        err_console.print(f"[red]오류:[/red] 파일을 찾을 수 없습니다: {file}")
        raise typer.Exit(1)

    with Progress(SpinnerColumn(spinner_name="line"), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("파싱 중...", total=None)
        collection = _load_collection(file)

    console.print(Panel(
        f"[green]✓[/green] 파싱 완료: [bold]{collection.total_clauses}개[/bold] 조항 추출",
        title=f"[bold]{file.name}[/bold]",
    ))

    table = Table(title="조항 목록", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("제목", style="yellow")
    table.add_column("내용 (앞 80자)")

    for clause in collection.clauses:
        table.add_row(
            clause.clause_id,
            clause.heading or "-",
            clause.text[:80] + ("..." if len(clause.text) > 80 else ""),
        )
    console.print(table)

    if output:
        from contract_review.report.json_report import save_json
        save_json(collection, output)
        console.print(f"\n[green]✓[/green] JSON 저장 완료: [bold]{output}[/bold]")


@app.command()
def review(
    file: Annotated[Path, typer.Argument(help="검토할 계약서 파일")],
    llm: LLMOption = "claude",
    output: OutputOption = None,
    contract_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="계약 유형 강제 지정 [employment|service|lease|nda|general]"),
    ] = None,
) -> None:
    """계약서를 한국 법령 기준으로 검토합니다."""
    if not file.exists():
        err_console.print(f"[red]오류:[/red] 파일을 찾을 수 없습니다: {file}")
        raise typer.Exit(1)

    from contract_review.analyzer.reviewer import Reviewer
    from contract_review.models.review import ContractType
    from contract_review.report.json_report import save_json
    from contract_review.report.md_report import save_markdown

    forced_type = ContractType(contract_type) if contract_type else None

    with Progress(SpinnerColumn(spinner_name="line"), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("파싱 중...", total=None)
        collection = _load_collection(file)
        progress.add_task(f"[{llm.upper()}] 검토 중...", total=None)
        client = get_client(llm)
        reviewer = Reviewer(client)
        report = reviewer.review(collection, forced_type)

    _print_review_summary(report)

    if output:
        if output.suffix == ".json":
            save_json(report, output)
        else:
            save_markdown(report, output)
        console.print(f"\n[green]✓[/green] 리포트 저장: [bold]{output}[/bold]")
    else:
        # 기본: Markdown을 stdout으로
        from contract_review.report.md_report import _review_to_markdown
        console.print("\n" + _review_to_markdown(report))


@app.command()
def diff(
    old_file: Annotated[Path, typer.Argument(help="이전 버전 계약서")],
    new_file: Annotated[Path, typer.Argument(help="새 버전 계약서")],
    llm: LLMOption = "claude",
    output: OutputOption = None,
) -> None:
    """두 계약서 버전을 비교합니다."""
    for f in [old_file, new_file]:
        if not f.exists():
            err_console.print(f"[red]오류:[/red] 파일을 찾을 수 없습니다: {f}")
            raise typer.Exit(1)

    from contract_review.analyzer.differ import Differ
    from contract_review.report.json_report import save_json
    from contract_review.report.md_report import save_markdown

    with Progress(SpinnerColumn(spinner_name="line"), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("이전 버전 파싱 중...", total=None)
        old_col = _load_collection(old_file)
        progress.add_task("새 버전 파싱 중...", total=None)
        new_col = _load_collection(new_file)
        progress.add_task(f"[{llm.upper()}] 비교 분석 중...", total=None)
        client = get_client(llm)
        differ = Differ(client)
        report = differ.diff(old_col, new_col)

    console.print(Panel(
        f"변경 항목: [bold]{len(report.items)}건[/bold]  "
        f"고위험: [red]{len(report.high_risk_items)}건[/red]",
        title="[bold]Diff 완료[/bold]",
    ))
    console.print(f"\n{report.summary}\n")

    if output:
        if output.suffix == ".json":
            save_json(report, output)
        else:
            save_markdown(report, output)
        console.print(f"[green]✓[/green] 리포트 저장: [bold]{output}[/bold]")
    else:
        from contract_review.report.md_report import _diff_to_markdown
        console.print(_diff_to_markdown(report))


@app.command()
def suggest(
    file: Annotated[Path, typer.Argument(help="계약서 파일")],
    clause: Annotated[str, typer.Option("--clause", "-c", help="개선할 조항 ID (예: '제3조', '1.2')")],
    llm: LLMOption = "claude",
    output: OutputOption = None,
) -> None:
    """특정 조항에 대한 개선 문구를 제안합니다."""
    if not file.exists():
        err_console.print(f"[red]오류:[/red] 파일을 찾을 수 없습니다: {file}")
        raise typer.Exit(1)

    from contract_review.analyzer.suggester import Suggester
    from contract_review.report.json_report import save_json

    with Progress(SpinnerColumn(spinner_name="line"), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        progress.add_task("파싱 중...", total=None)
        collection = _load_collection(file)
        progress.add_task(f"[{llm.upper()}] 개선 제안 생성 중...", total=None)
        client = get_client(llm)
        suggester = Suggester(client)
        result = suggester.suggest(collection, clause)

    console.print(Panel(
        f"[cyan]조항 ID:[/cyan] {result.get('clause_id', clause)}\n\n"
        f"[yellow]원본:[/yellow]\n{result.get('original_text', '')}\n\n"
        f"[green]개선 제안:[/green]\n{result.get('suggested_text', '')}",
        title="[bold]조항 개선 제안[/bold]",
        expand=False,
    ))

    if result.get("legal_basis"):
        console.print(f"\n[bold]법적 근거:[/bold] {', '.join(result['legal_basis'])}")
    if result.get("explanation"):
        console.print(f"\n[bold]설명:[/bold] {result['explanation']}")

    if output:
        save_json(result, output)
        console.print(f"\n[green]✓[/green] JSON 저장: [bold]{output}[/bold]")


def _print_review_summary(report) -> None:
    from contract_review.report.md_report import _RISK_EMOJI, _CONTRACT_TYPE_KO, _SEVERITY_KO

    risk_icon = _RISK_EMOJI.get(report.overall_risk, "⚪")
    contract_ko = _CONTRACT_TYPE_KO.get(report.contract_type.value, report.contract_type.value)

    console.print(Panel(
        f"[bold]계약 유형:[/bold] {contract_ko}  "
        f"[bold]전체 조항:[/bold] {report.total_clauses}개  "
        f"[bold]종합 위험도:[/bold] {risk_icon} {_SEVERITY_KO.get(report.overall_risk, report.overall_risk)}  "
        f"[bold]문제 발견:[/bold] {len(report.issues)}건",
        title=f"[bold]{Path(report.source_file).name}[/bold] 검토 완료",
    ))
    console.print(f"\n{report.summary}\n")

    if report.critical_issues:
        console.print(f"[red bold]🚨 심각(critical) 문제 {len(report.critical_issues)}건:[/red bold]")
        for issue in report.critical_issues:
            console.print(f"  • [{issue.clause_id}] {issue.description[:80]}")
        console.print()


if __name__ == "__main__":
    app()
