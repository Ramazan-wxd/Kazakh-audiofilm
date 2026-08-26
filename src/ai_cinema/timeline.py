"""Deterministic speech-free window derivation and one-event placement."""

from __future__ import annotations

from .models import AudioWindow, ScheduledNarration, TimeRange, Transcript, VisualEvent

GUARD_BAND_S = 0.350
NARRATION_PADDING_S = 0.200
MAX_EVENT_DELAY_S = 8.0


def derive_speech_free_windows(
    transcript: Transcript,
    media_duration_s: float,
    guard_band_s: float = GUARD_BAND_S,
) -> list[AudioWindow]:
    """Return complement intervals after merging guard-expanded speech segments."""
    guarded = sorted(
        (
            max(0.0, segment.time_range.start_s - guard_band_s),
            min(media_duration_s, segment.time_range.end_s + guard_band_s),
        )
        for segment in transcript.segments
    )
    merged: list[tuple[float, float]] = []
    for start_s, end_s in guarded:
        if not merged or start_s > merged[-1][1]:
            merged.append((start_s, end_s))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end_s))

    windows: list[AudioWindow] = []
    cursor = 0.0
    for start_s, end_s in merged:
        if start_s > cursor:
            windows.append(
                AudioWindow(
                    id=f"window-{len(windows) + 1}",
                    time_range=TimeRange(start_s=cursor, end_s=start_s),
                )
            )
        cursor = max(cursor, end_s)
    if cursor < media_duration_s:
        windows.append(
            AudioWindow(
                id=f"window-{len(windows) + 1}",
                time_range=TimeRange(start_s=cursor, end_s=media_duration_s),
            )
        )
    return windows


def select_safe_window(
    event: VisualEvent,
    narration_duration_s: float,
    windows: list[AudioWindow],
    padding_s: float = NARRATION_PADDING_S,
    max_delay_s: float = MAX_EVENT_DELAY_S,
) -> ScheduledNarration | None:
    """Place one narration at the earliest fitting, post-event safe window."""
    required_s = narration_duration_s + padding_s
    latest_start_s = event.time_range.end_s + max_delay_s
    for window in windows:
        start_s = max(window.time_range.start_s, event.time_range.end_s)
        end_s = start_s + required_s
        if start_s <= latest_start_s and end_s <= window.time_range.end_s:
            return ScheduledNarration(
                event_id=event.id,
                narration_range=TimeRange(start_s=start_s, end_s=start_s + narration_duration_s),
                source_window_id=window.id,
                reason="earliest post-event speech-free window that fits narration and padding",
            )
    return None
