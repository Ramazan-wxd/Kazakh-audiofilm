from __future__ import annotations

import subprocess
import wave
from pathlib import Path
from shutil import which

import pytest

from ai_cinema.media import MediaBackend


@pytest.fixture()
def ffmpeg_bins() -> tuple[str, str]:
    ffmpeg_bin = which("ffmpeg")
    ffprobe_bin = which("ffprobe")
    if not ffmpeg_bin or not ffprobe_bin:
        pytest.skip("FFmpeg and ffprobe must both be available on PATH")
    return ffmpeg_bin, ffprobe_bin


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True, capture_output=True, text=True)


def test_media_backend_extracts_and_renders_synthetic_media(
    tmp_path: Path, ffmpeg_bins: tuple[str, str]
) -> None:
    ffmpeg_bin, ffprobe_bin = ffmpeg_bins
    source = tmp_path / "synthetic-source.mp4"
    narration = tmp_path / "narration.wav"
    analysis = tmp_path / "analysis.wav"
    output = tmp_path / "output.mp4"
    _run(
        [
            ffmpeg_bin,
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=160x120:rate=24:duration=16",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:sample_rate=48000:duration=16",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            "-shortest",
            str(source),
        ]
    )
    with wave.open(str(narration), "wb") as audio_file:
        audio_file.setnchannels(1)
        audio_file.setsampwidth(2)
        audio_file.setframerate(24000)
        audio_file.writeframes(b"\x00\x00" * 24000)

    media = MediaBackend(ffmpeg_bin, ffprobe_bin)
    assert media.probe(source).duration_s == pytest.approx(16, abs=0.1)
    media.extract_analysis_audio(source, analysis)
    assert media.measure_duration(analysis) == pytest.approx(16, abs=0.1)
    media.render_original_runtime(source, narration, 4, 1, output)

    assert output.is_file()
    assert media.probe(output).duration_s == pytest.approx(16, abs=0.1)
