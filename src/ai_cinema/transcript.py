"""faster-whisper transcription adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from .errors import AiCinemaError
from .models import TimeRange, Transcript, TranscriptSegment, TranscriptWord


class TranscriptionError(AiCinemaError):
    """Raised when speech recognition cannot complete."""


class Transcriber(Protocol):
    def transcribe(self, audio_path: Path) -> Transcript: ...


class FasterWhisperTranscriber:
    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def transcribe(self, audio_path: Path) -> Transcript:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise TranscriptionError("faster-whisper is not installed") from exc

        try:
            model = WhisperModel(self.model_name, device="auto", compute_type="int8")
            raw_segments, info = model.transcribe(str(audio_path), word_timestamps=True)
            segments: list[TranscriptSegment] = []
            for raw_segment in raw_segments:
                words = [
                    TranscriptWord(
                        text=word.word,
                        time_range=TimeRange(start_s=word.start, end_s=word.end),
                    )
                    for word in (raw_segment.words or [])
                    if word.start is not None and word.end is not None and word.end > word.start
                ]
                if raw_segment.end > raw_segment.start:
                    segments.append(
                        TranscriptSegment(
                            text=raw_segment.text.strip(),
                            time_range=TimeRange(start_s=raw_segment.start, end_s=raw_segment.end),
                            words=words,
                        )
                    )
            return Transcript(language=info.language, segments=segments)
        except Exception as exc:  # Provider errors differ by runtime/backend.
            raise TranscriptionError(f"Transcription failed: {exc}") from exc
