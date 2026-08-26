"""Azure Kazakh text-to-speech behind the small TtsProvider contract."""

from __future__ import annotations

import wave
from pathlib import Path
from typing import Protocol

from .errors import AiCinemaError
from .models import NarrationAsset


class TtsError(AiCinemaError):
    """Raised when narration synthesis cannot complete."""


class TtsProvider(Protocol):
    def synthesize(self, event_id: str, text: str, output_path: Path) -> NarrationAsset: ...


class AzureTtsProvider:
    def __init__(self, key: str, region: str, voice: str) -> None:
        self.key = key
        self.region = region
        self.voice = voice

    def synthesize(self, event_id: str, text: str, output_path: Path) -> NarrationAsset:
        try:
            import azure.cognitiveservices.speech as speechsdk
        except ImportError as exc:
            raise TtsError("azure-cognitiveservices-speech is not installed") from exc

        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            speech_config = speechsdk.SpeechConfig(subscription=self.key, region=self.region)
            speech_config.speech_synthesis_voice_name = self.voice
            speech_config.set_speech_synthesis_output_format(
                speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm
            )
            audio_config = speechsdk.audio.AudioOutputConfig(filename=str(output_path))
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config, audio_config=audio_config
            )
            result = synthesizer.speak_text_async(text).get()
            if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
                details = getattr(result, "cancellation_details", None)
                raise TtsError(f"Azure Speech synthesis failed: {details or result.reason}")
            with wave.open(str(output_path), "rb") as audio_file:
                duration_s = audio_file.getnframes() / audio_file.getframerate()
            return NarrationAsset(
                event_id=event_id,
                text=text,
                audio_path=output_path,
                duration_s=duration_s,
            )
        except TtsError:
            raise
        except Exception as exc:  # Azure SDK exposes several backend-specific errors.
            raise TtsError(f"Azure Speech synthesis failed: {exc}") from exc
