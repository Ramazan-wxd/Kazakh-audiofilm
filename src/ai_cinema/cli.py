"""Command-line entry point for the Milestone 1 vertical slice."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from .config import Settings
from .errors import AiCinemaError
from .media import MediaBackend
from .pipeline import run_pipeline
from .transcript import FasterWhisperTranscriber
from .tts import AzureTtsProvider
from .vision import GeminiVisionProvider

app = typer.Typer(
    add_completion=False,
    help="Generate a Kazakh audio description for a short video.",
)


@app.callback()
def command_group() -> None:
    """AI Cinema commands."""


@app.command()
def describe(
    input_path: Annotated[Path, typer.Argument(help="Authorized 15–45 second input video.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output MP4 path.")],
    work_dir: Annotated[Path, typer.Option(help="Local, ignored artifact directory.")] = Path(
        ".ai-cinema"
    ),
) -> None:
    """Run the complete Milestone 1 original-runtime pipeline."""
    settings = Settings.from_environment()
    missing = [
        name
        for name, value in (
            ("GEMINI_API_KEY", settings.gemini_api_key),
            ("AZURE_SPEECH_KEY", settings.azure_speech_key),
            ("AZURE_SPEECH_REGION", settings.azure_speech_region),
        )
        if not value
    ]
    if missing:
        typer.echo(f"Missing required environment variable(s): {', '.join(missing)}", err=True)
        raise typer.Exit(code=2)

    try:
        manifest = run_pipeline(
            input_path=input_path,
            output_path=output,
            work_dir=work_dir,
            settings=settings,
            media=MediaBackend(settings.ffmpeg_bin, settings.ffprobe_bin),
            transcriber=FasterWhisperTranscriber(settings.asr_model),
            vision=GeminiVisionProvider(settings.gemini_api_key or "", settings.gemini_model),
            tts=AzureTtsProvider(
                settings.azure_speech_key or "",
                settings.azure_speech_region or "",
                settings.tts_voice,
            ),
            report=typer.echo,
        )
    except AiCinemaError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Manifest: {manifest.artifacts['manifest']}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
