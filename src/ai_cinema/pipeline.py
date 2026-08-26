"""The intentionally small Milestone 1 end-to-end pipeline."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path

from .config import Settings
from .errors import AiCinemaError
from .media import MediaBackend
from .models import RunManifest, TimeRange
from .timeline import derive_speech_free_windows, select_safe_window
from .transcript import Transcriber
from .tts import TtsProvider
from .vision import VisionProvider

MIN_INPUT_DURATION_S = 15.0
MAX_INPUT_DURATION_S = 45.0


class PipelineError(AiCinemaError):
    """Raised when a valid Milestone 1 result cannot be rendered."""


def run_pipeline(
    input_path: Path,
    output_path: Path,
    work_dir: Path,
    settings: Settings,
    media: MediaBackend,
    transcriber: Transcriber,
    vision: VisionProvider,
    tts: TtsProvider,
    report: Callable[[str], None] | None = None,
) -> RunManifest:
    def say(message: str) -> None:
        if report is not None:
            report(message)

    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if not input_path.is_file():
        raise PipelineError(f"Input video does not exist: {input_path}")

    media.ensure_available()
    say("Probing input video")
    media_info = media.probe(input_path)
    if not media_info.has_audio:
        raise PipelineError("Input video must contain an audio stream")
    if not MIN_INPUT_DURATION_S <= media_info.duration_s <= MAX_INPUT_DURATION_S:
        raise PipelineError(
            f"Milestone 1 accepts videos between {MIN_INPUT_DURATION_S:g} and "
            f"{MAX_INPUT_DURATION_S:g} seconds; input is {media_info.duration_s:.2f} seconds"
        )

    input_hash = _sha256(input_path)
    run_dir = work_dir.resolve() / input_hash[:16]
    audio_path = run_dir / "analysis.wav"
    narration_path = run_dir / "narration" / "event-1.wav"
    manifest_path = run_dir / "manifest.json"

    say("Extracting analysis audio")
    media.extract_analysis_audio(input_path, audio_path)
    say(f"Transcribing speech with faster-whisper ({settings.asr_model})")
    transcript = transcriber.transcribe(audio_path)
    windows = derive_speech_free_windows(transcript, media_info.duration_s)
    if not windows:
        raise PipelineError("No speech-free windows are available after guard bands")

    say("Analyzing the authorized video with Gemini")
    event = vision.analyze(input_path, TimeRange(start_s=0, end_s=media_info.duration_s))
    if event is None:
        raise PipelineError("Gemini found no salient visual event suitable for narration")

    say("Synthesizing Kazakh narration with Azure Speech")
    narration = tts.synthesize(event.id, event.kazakh_description, narration_path)
    schedule = select_safe_window(event, narration.duration_s, windows)
    if schedule is None:
        raise PipelineError(
            "No speech-free window can fit the narration within eight seconds after the event"
        )

    say(f"Rendering narration at {schedule.narration_range.start_s:.2f}s")
    media.render_original_runtime(
        input_path=input_path,
        narration_path=narration.audio_path,
        narration_start_s=schedule.narration_range.start_s,
        narration_duration_s=narration.duration_s,
        output_path=output_path,
    )
    manifest = RunManifest(
        input_path=input_path,
        input_sha256=input_hash,
        output_path=output_path,
        effective_config=settings.public_values(),
        tool_versions={"ffmpeg": media.version()},
        artifacts={
            "analysis_audio": audio_path,
            "narration": narration.audio_path,
            "manifest": manifest_path,
        },
        event=event,
        schedule=schedule,
    )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    say(f"Completed: {output_path}")
    return manifest


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
