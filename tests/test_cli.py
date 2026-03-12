"""CLI 동작 테스트."""

from pathlib import Path

from typer.testing import CliRunner

from contract_review.cli import app
from contract_review.models.clause import ClauseCollection
from contract_review.models.review import ContractType, ReviewReport


runner = CliRunner()


def test_review_help_shows_ack_risk_option():
    result = runner.invoke(app, ["review", "--help"])

    assert result.exit_code == 0
    assert "--ack-risk" in result.output
    assert "--redact" in result.output


def test_review_requires_ack_risk_in_noninteractive_mode(monkeypatch, tmp_path: Path):
    contract_file = tmp_path / "contract.txt"
    contract_file.write_text("제1조 (목적)\n내용", encoding="utf-8")

    monkeypatch.setattr("contract_review.cli._is_interactive_terminal", lambda: False)
    monkeypatch.setattr(
        "contract_review.cli._load_collection",
        lambda _path: (_ for _ in ()).throw(AssertionError("should not parse without ack")),
    )

    result = runner.invoke(app, ["review", str(contract_file)])

    assert result.exit_code == 1
    assert "--ack-risk" in result.output


def test_review_runs_with_ack_risk(monkeypatch, tmp_path: Path):
    contract_file = tmp_path / "contract.txt"
    output_file = tmp_path / "report.json"
    contract_file.write_text("제1조 (목적)\n내용", encoding="utf-8")

    collection = ClauseCollection(source_file=str(contract_file), clauses=[])

    monkeypatch.setattr("contract_review.cli._is_interactive_terminal", lambda: False)
    monkeypatch.setattr("contract_review.cli._load_collection", lambda _path: collection)
    monkeypatch.setattr("contract_review.cli.get_client", lambda _llm: object())
    monkeypatch.setattr("contract_review.cli._print_review_summary", lambda _report: None)

    def fake_review(self, loaded_collection, forced_type):
        assert loaded_collection is collection
        assert forced_type is None
        return ReviewReport(
            source_file=str(contract_file),
            contract_type=ContractType.GENERAL,
            total_clauses=0,
            issues=[],
            overall_risk="low",
            summary="ok",
        )

    monkeypatch.setattr("contract_review.analyzer.reviewer.Reviewer.review", fake_review)

    result = runner.invoke(
        app,
        ["review", str(contract_file), "--ack-risk", "--output", str(output_file)],
    )

    assert result.exit_code == 0
    assert output_file.exists()


def test_review_passes_redact_flag(monkeypatch, tmp_path: Path):
    contract_file = tmp_path / "contract.txt"
    output_file = tmp_path / "report.json"
    contract_file.write_text("제1조 (목적)\n내용", encoding="utf-8")

    collection = ClauseCollection(source_file=str(contract_file), clauses=[])
    captured: dict[str, bool] = {}

    monkeypatch.setattr("contract_review.cli._is_interactive_terminal", lambda: False)
    monkeypatch.setattr("contract_review.cli._load_collection", lambda _path: collection)
    monkeypatch.setattr("contract_review.cli.get_client", lambda _llm: object())
    monkeypatch.setattr("contract_review.cli._print_review_summary", lambda _report: None)

    class FakeReviewer:
        def __init__(self, _client, redact_sensitive: bool = False):
            captured["redact_sensitive"] = redact_sensitive

        def review(self, loaded_collection, forced_type):
            assert loaded_collection is collection
            assert forced_type is None
            return ReviewReport(
                source_file=str(contract_file),
                contract_type=ContractType.GENERAL,
                total_clauses=0,
                issues=[],
                overall_risk="low",
                summary="ok",
            )

    monkeypatch.setattr("contract_review.analyzer.reviewer.Reviewer", FakeReviewer)

    result = runner.invoke(
        app,
        ["review", str(contract_file), "--ack-risk", "--redact", "--output", str(output_file)],
    )

    assert result.exit_code == 0
    assert captured["redact_sensitive"] is True
    assert output_file.exists()
