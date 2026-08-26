from typer.testing import CliRunner

from ai_cinema.cli import app


def test_cli_exposes_describe_subcommand() -> None:
    result = CliRunner().invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "describe" in result.stdout


def test_describe_fails_before_work_without_credentials(monkeypatch) -> None:
    for name in ("GEMINI_API_KEY", "AZURE_SPEECH_KEY", "AZURE_SPEECH_REGION"):
        monkeypatch.delenv(name, raising=False)

    result = CliRunner().invoke(app, ["describe", "missing.mp4", "--output", "output.mp4"])

    assert result.exit_code == 2
    assert "Missing required environment variable" in result.stderr
