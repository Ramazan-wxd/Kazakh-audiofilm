"""Environment-backed settings for the small local CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str | None
    azure_speech_key: str | None
    azure_speech_region: str | None
    asr_model: str
    gemini_model: str
    tts_voice: str
    ffmpeg_bin: str
    ffprobe_bin: str

    @classmethod
    def from_environment(cls) -> Settings:
        load_dotenv()
        return cls(
            gemini_api_key=os.getenv("GEMINI_API_KEY"),
            azure_speech_key=os.getenv("AZURE_SPEECH_KEY"),
            azure_speech_region=os.getenv("AZURE_SPEECH_REGION"),
            asr_model=os.getenv("AI_CINEMA_ASR_MODEL", "small"),
            gemini_model=os.getenv("AI_CINEMA_GEMINI_MODEL", "gemini-2.5-flash"),
            tts_voice=os.getenv("AI_CINEMA_TTS_VOICE", "kk-KZ-AigulNeural"),
            ffmpeg_bin=os.getenv("FFMPEG_BIN", "ffmpeg"),
            ffprobe_bin=os.getenv("FFPROBE_BIN", "ffprobe"),
        )

    def public_values(self) -> dict[str, str | float | int]:
        return {
            "asr_model": self.asr_model,
            "gemini_model": self.gemini_model,
            "tts_voice": self.tts_voice,
            "ffmpeg_bin": self.ffmpeg_bin,
            "ffprobe_bin": self.ffprobe_bin,
        }
