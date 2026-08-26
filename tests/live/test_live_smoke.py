"""Explicit opt-in test: never runs without keys and an authorized local video."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ai_cinema.config import Settings
from ai_cinema.media import MediaBackend
from ai_cinema.pipeline import run_pipeline
from ai_cinema.transcript import FasterWhisperTranscriber
from ai_cinema.tts import AzureTtsProvider
from ai_cinema.vision import GeminiVisionProvider

pytestmark = pytest.mark.live


def test_live_vertical_slice(tmp_path: Path) -> None:
    if os.getenv("AI_CINEMA_RUN_LIVE") != "1":
        pytest.skip("Set AI_CINEMA_RUN_LIVE=1 to enable credentialed smoke testing")
    settings = Settings.from_environment()
    if not all((settings.gemini_api_key, settings.azure_speech_key, settings.azure_speech_region)):
        pytest.skip("Gemini and Azure Speech credentials are required")
    source_value = os.getenv("AI_CINEMA_LIVE_VIDEO")
    if not source_value:
        pytest.skip("Set AI_CINEMA_LIVE_VIDEO to an authorized 15–45 second video")
    source = Path(source_value)
    if not source.is_file():
        pytest.skip("AI_CINEMA_LIVE_VIDEO does not point to a local file")

    output = tmp_path / "live-output.mp4"
    manifest = run_pipeline(
        input_path=source,
        output_path=output,
        work_dir=tmp_path / "work",
        settings=settings,
        media=MediaBackend(settings.ffmpeg_bin, settings.ffprobe_bin),
        transcriber=FasterWhisperTranscriber(settings.asr_model),
        vision=GeminiVisionProvider(settings.gemini_api_key or "", settings.gemini_model),
        tts=AzureTtsProvider(
            settings.azure_speech_key or "",
            settings.azure_speech_region or "",
            settings.tts_voice,
        ),
    )

    assert output.is_file()
    assert manifest.artifacts["manifest"].is_file()
