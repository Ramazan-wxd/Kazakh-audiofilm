from __future__ import annotations

import subprocess
from pathlib import Path
from shutil import which

import pytest

from ai_cinema.config import Settings
from ai_cinema.media import MediaBackend
from ai_cinema.models import TimeRange, Transcript, TranscriptSegment, VisualEvent
from ai_cinema.pipeline import run_pipeline
from tests.conftest import FakeTranscriber, FakeTtsProvider, FakeVisionProvider


@pytest.fixture()
def media_backend() -> MediaBackend:
    ffmpeg_bin = which("ffmpeg")
    ffprobe_bin = which("ffprobe")
    if not ffmpeg_bin or not ffprobe_bin:
        pytest.skip("FFmpeg and ffprobe must both be available on PATH")
    return MediaBackend(ffmpeg_bin, ffprobe_bin)


def test_full_pipeline_with_synthetic_media_and_mocked_cloud_providers(
    tmp_path: Path, media_backend: MediaBackend
) -> None:
    source = tmp_path / "synthetic.mp4"
    subprocess.run(
        [
            media_backend.ffmpeg_bin,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=160x120:rate=24:duration=20",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=20",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            "-shortest",
            str(source),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    settings = Settings(
        gemini_api_key="mock",
        azure_speech_key="mock",
        azure_speech_region="mock",
        asr_model="small",
        gemini_model="mock-model",
        tts_voice="kk-KZ-AigulNeural",
        ffmpeg_bin=media_backend.ffmpeg_bin,
        ffprobe_bin=media_backend.ffprobe_bin,
    )
    event = VisualEvent(
        id="event-1",
        time_range=TimeRange(start_s=5, end_s=6),
        facts=["A test pattern changes."],
        kazakh_description="Көрініс өзгереді.",
        salience=3,
        confidence=0.9,
        evidence_times_s=[5.5],
    )
    transcript = Transcript(
        language="en",
        segments=[TranscriptSegment(text="speech", time_range=TimeRange(start_s=1, end_s=3))],
    )
    output = tmp_path / "described.mp4"

    manifest = run_pipeline(
        input_path=source,
        output_path=output,
        work_dir=tmp_path / "work",
        settings=settings,
        media=media_backend,
        transcriber=FakeTranscriber(transcript),
        vision=FakeVisionProvider(event),
        tts=FakeTtsProvider(duration_s=1),
    )

    assert output.is_file()
    assert media_backend.probe(output).duration_s == pytest.approx(20, abs=0.1)
    assert manifest.artifacts["manifest"].is_file()
    assert manifest.schedule.narration_range == TimeRange(start_s=6, end_s=7)
