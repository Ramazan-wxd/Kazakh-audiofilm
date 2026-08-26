"""Small, validated data contracts for the Milestone 1 pipeline."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class TimeRange(BaseModel):
    start_s: float = Field(ge=0)
    end_s: float = Field(gt=0)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> TimeRange:
        if self.end_s <= self.start_s:
            raise ValueError("end_s must be greater than start_s")
        return self

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


class TranscriptWord(BaseModel):
    text: str
    time_range: TimeRange


class TranscriptSegment(BaseModel):
    text: str
    time_range: TimeRange
    words: list[TranscriptWord] = Field(default_factory=list)


class Transcript(BaseModel):
    language: str
    segments: list[TranscriptSegment]


class VisualEvent(BaseModel):
    id: str
    time_range: TimeRange
    facts: list[str] = Field(min_length=1, max_length=3)
    kazakh_description: str = Field(min_length=1, max_length=120)
    salience: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0, le=1)
    evidence_times_s: list[float] = Field(min_length=1, max_length=3)


class AudioWindow(BaseModel):
    id: str
    time_range: TimeRange
    speech_free: bool = True


class NarrationAsset(BaseModel):
    event_id: str
    text: str
    audio_path: Path
    duration_s: float = Field(gt=0)


class ScheduledNarration(BaseModel):
    event_id: str
    narration_range: TimeRange
    source_window_id: str
    status: str = "scheduled"
    reason: str


class RunManifest(BaseModel):
    input_path: Path
    input_sha256: str
    output_path: Path
    effective_config: dict[str, str | float | int]
    tool_versions: dict[str, str]
    artifacts: dict[str, Path]
    event: VisualEvent
    schedule: ScheduledNarration
