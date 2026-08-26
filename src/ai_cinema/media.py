"""Minimal FFmpeg operations needed by the first vertical slice."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .errors import AiCinemaError


class MediaError(AiCinemaError):
    """Raised when FFmpeg cannot complete a requested operation."""


@dataclass(frozen=True)
class MediaInfo:
    duration_s: float
    has_audio: bool


class MediaBackend:
    def __init__(self, ffmpeg_bin: str, ffprobe_bin: str) -> None:
        self.ffmpeg_bin = ffmpeg_bin
        self.ffprobe_bin = ffprobe_bin

    def ensure_available(self) -> None:
        missing = [
            name
            for name in (self.ffmpeg_bin, self.ffprobe_bin)
            if shutil.which(name) is None and not Path(name).is_file()
        ]
        if missing:
            raise MediaError(
                "Required media executable(s) not found: "
                f"{', '.join(missing)}. Set FFMPEG_BIN/FFPROBE_BIN or add FFmpeg to PATH."
            )

    def probe(self, input_path: Path) -> MediaInfo:
        output = self._run(
            [
                self.ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration:stream=codec_type",
                "-of",
                "json",
                str(input_path),
            ]
        )
        try:
            data = json.loads(output.stdout)
            duration_s = float(data["format"]["duration"])
            has_audio = any(stream.get("codec_type") == "audio" for stream in data["streams"])
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise MediaError(f"Could not read media metadata for {input_path}") from exc
        if duration_s <= 0:
            raise MediaError(f"Input video has no positive duration: {input_path}")
        return MediaInfo(duration_s=duration_s, has_audio=has_audio)

    def extract_analysis_audio(self, input_path: Path, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        self._run(
            [
                self.ffmpeg_bin,
                "-y",
                "-i",
                str(input_path),
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-c:a",
                "pcm_s16le",
                str(output_path),
            ]
        )

    def measure_duration(self, audio_path: Path) -> float:
        output = self._run(
            [
                self.ffprobe_bin,
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(audio_path),
            ]
        )
        try:
            duration_s = float(output.stdout.strip())
        except ValueError as exc:
            raise MediaError(f"Could not measure narration duration: {audio_path}") from exc
        if duration_s <= 0:
            raise MediaError(f"Narration has no positive duration: {audio_path}")
        return duration_s

    def render_original_runtime(
        self,
        input_path: Path,
        narration_path: Path,
        narration_start_s: float,
        narration_duration_s: float,
        output_path: Path,
    ) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        narration_end_s = narration_start_s + narration_duration_s
        delay_ms = round(narration_start_s * 1000)
        duck_factor = 10 ** (-12 / 20)
        filter_complex = (
            f"[0:a]volume=volume={duck_factor:.9f}:"
            f"enable='between(t,{narration_start_s:.3f},{narration_end_s:.3f})'[ducked];"
            f"[1:a]adelay={delay_ms}:all=1[narration];"
            "[ducked][narration]amix=inputs=2:duration=first:dropout_transition=0[mixed]"
        )
        self._run(
            [
                self.ffmpeg_bin,
                "-y",
                "-i",
                str(input_path),
                "-i",
                str(narration_path),
                "-filter_complex",
                filter_complex,
                "-map",
                "0:v:0",
                "-map",
                "[mixed]",
                "-c:v",
                "copy",
                "-c:a",
                "aac",
                "-b:a",
                "192k",
                "-movflags",
                "+faststart",
                str(output_path),
            ]
        )

    def version(self) -> str:
        output = self._run([self.ffmpeg_bin, "-version"])
        return output.stdout.splitlines()[0]

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(command, check=True, text=True, capture_output=True)
        except FileNotFoundError as exc:
            raise MediaError(f"Media executable not found: {command[0]}") from exc
        except subprocess.CalledProcessError as exc:
            details = exc.stderr.strip() or exc.stdout.strip()
            raise MediaError(f"Media command failed: {' '.join(command[:3])}. {details}") from exc
