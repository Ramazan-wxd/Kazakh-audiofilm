"""Gemini native-video analysis behind the small VisionProvider contract."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Protocol, cast

from pydantic import BaseModel, Field

from .errors import AiCinemaError
from .models import TimeRange, VisualEvent


class VisionError(AiCinemaError):
    """Raised when the visual analysis provider cannot return a valid event."""


class VisionProvider(Protocol):
    def analyze(self, clip_path: Path, clip_range: TimeRange) -> VisualEvent | None: ...


class GeminiEventPayload(BaseModel):
    event_start_s: float = Field(ge=0)
    event_end_s: float = Field(gt=0)
    facts: list[str] = Field(min_length=1, max_length=3)
    kazakh_description: str = Field(min_length=1, max_length=120)
    salience: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    evidence_times_s: list[float] = Field(min_length=1, max_length=3)


class GeminiResponsePayload(BaseModel):
    event: GeminiEventPayload | None = None


class GeminiVisionProvider:
    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    def analyze(self, clip_path: Path, clip_range: TimeRange) -> VisualEvent | None:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise VisionError("google-genai is not installed") from exc

        client = genai.Client(api_key=self.api_key)
        uploaded: Any | None = None
        try:
            uploaded = client.files.upload(file=str(clip_path))
            self._wait_until_ready(client, uploaded)
            response = client.models.generate_content(
                model=self.model,
                contents=cast(Any, [uploaded, self._prompt(clip_range.duration_s)]),
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiResponsePayload,
                    temperature=0,
                ),
            )
            if not response.text:
                raise VisionError("Gemini returned no structured response text")
            payload = GeminiResponsePayload.model_validate(json.loads(response.text))
            if payload.event is None:
                return None
            event = payload.event
            if event.event_end_s <= event.event_start_s:
                raise VisionError("Gemini returned an event with an invalid time range")
            if event.event_end_s > clip_range.duration_s + 0.1:
                raise VisionError("Gemini event timestamp exceeds the uploaded clip duration")
            return VisualEvent(
                id="event-1",
                time_range=TimeRange(
                    start_s=clip_range.start_s + event.event_start_s,
                    end_s=clip_range.start_s + event.event_end_s,
                ),
                facts=event.facts,
                kazakh_description=event.kazakh_description,
                salience=event.salience,
                confidence=event.confidence,
                evidence_times_s=[clip_range.start_s + item for item in event.evidence_times_s],
            )
        except VisionError:
            raise
        except Exception as exc:  # SDK errors are not stable across versions.
            raise VisionError(f"Gemini analysis failed: {exc}") from exc
        finally:
            if uploaded is not None:
                try:
                    client.files.delete(name=uploaded.name)
                except Exception:
                    pass

    @staticmethod
    def _wait_until_ready(client: Any, uploaded: Any) -> None:
        while getattr(getattr(uploaded, "state", None), "name", None) == "PROCESSING":
            time.sleep(2)
            uploaded = client.files.get(name=uploaded.name)
        state = getattr(getattr(uploaded, "state", None), "name", None)
        if state not in {None, "ACTIVE"}:
            raise VisionError(f"Gemini file processing failed with state {state}")

    @staticmethod
    def _prompt(clip_duration_s: float) -> str:
        return f"""
Analyze this {clip_duration_s:.1f}-second video for accessibility narration.
Return exactly one visually salient event, or null when none deserves narration.
Use only visible evidence; do not describe dialogue, infer motives, name unknown people,
or repeat existing audio. Event timestamps are seconds relative to this uploaded clip.
The Kazakh description must be factual, concise (at most ten words), and written in
Kazakh Cyrillic. Return JSON matching the supplied schema.
""".strip()
