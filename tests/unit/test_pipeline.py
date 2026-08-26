from pathlib import Path

import pytest

from ai_cinema.config import Settings
from ai_cinema.models import TimeRange, Transcript, TranscriptSegment, VisualEvent
from ai_cinema.pipeline import PipelineError, run_pipeline
from tests.conftest import FakeMediaBackend, FakeTranscriber, FakeTtsProvider, FakeVisionProvider


def _settings() -> Settings:
    return Settings(
        gemini_api_key="not-a-real-key",
        azure_speech_key="not-a-real-key",
        azure_speech_region="test-region",
        asr_model="small",
        gemini_model="test-model",
        tts_voice="kk-KZ-AigulNeural",
        ffmpeg_bin="ffmpeg",
        ffprobe_bin="ffprobe",
    )


def _event() -> VisualEvent:
    return VisualEvent(
        id="event-1",
        time_range=TimeRange(start_s=3, end_s=4),
        facts=["A person opens a door."],
        kazakh_description="Адам есікті ашады.",
        salience=4,
        confidence=0.9,
        evidence_times_s=[3.5],
    )


def test_pipeline_renders_and_writes_manifest(tmp_path: Path) -> None:
    source = tmp_path / "authorized.mp4"
    source.write_bytes(b"authorized fixture")
    output = tmp_path / "output.mp4"
    media = FakeMediaBackend()
    transcript = Transcript(
        language="en",
        segments=[TranscriptSegment(text="dialogue", time_range=TimeRange(start_s=10, end_s=20))],
    )

    manifest = run_pipeline(
        input_path=source,
        output_path=output,
        work_dir=tmp_path / "work",
        settings=_settings(),
        media=media,  # type: ignore[arg-type]
        transcriber=FakeTranscriber(transcript),
        vision=FakeVisionProvider(_event()),
        tts=FakeTtsProvider(duration_s=1),
    )

    assert output.read_bytes() == b"rendered mp4 placeholder"
    assert manifest.artifacts["manifest"].is_file()
    assert manifest.schedule.narration_range == TimeRange(start_s=4, end_s=5)
    assert media.render_calls[0]["narration_start_s"] == 4


def test_pipeline_refuses_input_outside_milestone_duration(tmp_path: Path) -> None:
    source = tmp_path / "too-long.mp4"
    source.write_bytes(b"fixture")
    transcript = Transcript(language="en", segments=[])

    with pytest.raises(PipelineError, match="between 15 and 45 seconds"):
        run_pipeline(
            input_path=source,
            output_path=tmp_path / "output.mp4",
            work_dir=tmp_path / "work",
            settings=_settings(),
            media=FakeMediaBackend(duration_s=46),  # type: ignore[arg-type]
            transcriber=FakeTranscriber(transcript),
            vision=FakeVisionProvider(_event()),
            tts=FakeTtsProvider(),
        )


def test_pipeline_reports_when_no_window_fits(tmp_path: Path) -> None:
    source = tmp_path / "authorized.mp4"
    source.write_bytes(b"fixture")
    transcript = Transcript(
        language="en",
        segments=[TranscriptSegment(text="dialogue", time_range=TimeRange(start_s=0, end_s=30))],
    )

    with pytest.raises(PipelineError, match="No speech-free window"):
        run_pipeline(
            input_path=source,
            output_path=tmp_path / "output.mp4",
            work_dir=tmp_path / "work",
            settings=_settings(),
            media=FakeMediaBackend(),  # type: ignore[arg-type]
            transcriber=FakeTranscriber(transcript),
            vision=FakeVisionProvider(_event()),
            tts=FakeTtsProvider(),
        )
