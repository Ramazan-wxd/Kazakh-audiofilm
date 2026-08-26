from __future__ import annotations

import wave
from pathlib import Path

from ai_cinema.media import MediaInfo
from ai_cinema.models import NarrationAsset, TimeRange, Transcript, VisualEvent


class FakeMediaBackend:
    def __init__(self, duration_s: float = 30.0) -> None:
        self.duration_s = duration_s
        self.render_calls: list[dict[str, object]] = []

    def ensure_available(self) -> None:
        return None

    def probe(self, input_path: Path) -> MediaInfo:
        return MediaInfo(duration_s=self.duration_s, has_audio=True)

    def extract_analysis_audio(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"analysis audio placeholder")

    def render_original_runtime(
        self,
        input_path: Path,
        narration_path: Path,
        narration_start_s: float,
        narration_duration_s: float,
        output_path: Path,
    ) -> None:
        self.render_calls.append(
            {
                "input_path": input_path,
                "narration_path": narration_path,
                "narration_start_s": narration_start_s,
                "narration_duration_s": narration_duration_s,
            }
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"rendered mp4 placeholder")

    def version(self) -> str:
        return "ffmpeg fake 1.0"


class FakeTranscriber:
    def __init__(self, transcript: Transcript) -> None:
        self.transcript = transcript

    def transcribe(self, audio_path: Path) -> Transcript:
        return self.transcript


class FakeVisionProvider:
    def __init__(self, event: VisualEvent | None) -> None:
        self.event = event
        self.calls: list[tuple[Path, TimeRange]] = []

    def analyze(self, clip_path: Path, clip_range: TimeRange) -> VisualEvent | None:
        self.calls.append((clip_path, clip_range))
        return self.event


class FakeTtsProvider:
    def __init__(self, duration_s: float = 1.0) -> None:
        self.duration_s = duration_s
        self.calls: list[tuple[str, str]] = []

    def synthesize(self, event_id: str, text: str, output_path: Path) -> NarrationAsset:
        self.calls.append((event_id, text))
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as audio_file:
            audio_file.setnchannels(1)
            audio_file.setsampwidth(2)
            audio_file.setframerate(16000)
            audio_file.writeframes(b"\x00\x00" * round(16000 * self.duration_s))
        return NarrationAsset(
            event_id=event_id,
            text=text,
            audio_path=output_path,
            duration_s=self.duration_s,
        )
