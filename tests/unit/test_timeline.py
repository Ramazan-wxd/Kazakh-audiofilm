from ai_cinema.models import TimeRange, Transcript, TranscriptSegment, VisualEvent
from ai_cinema.timeline import derive_speech_free_windows, select_safe_window


def test_speech_windows_include_350ms_guard_bands() -> None:
    transcript = Transcript(
        language="en",
        segments=[
            TranscriptSegment(text="hello", time_range=TimeRange(start_s=1, end_s=2)),
            TranscriptSegment(text="world", time_range=TimeRange(start_s=4, end_s=5)),
        ],
    )

    windows = derive_speech_free_windows(transcript, media_duration_s=10)

    assert [(item.time_range.start_s, item.time_range.end_s) for item in windows] == [
        (0, 0.65),
        (2.35, 3.65),
        (5.35, 10),
    ]


def test_scheduler_uses_earliest_post_event_window_that_fits() -> None:
    event = VisualEvent(
        id="event-1",
        time_range=TimeRange(start_s=2.5, end_s=3),
        facts=["A door opens."],
        kazakh_description="Есік ашылады.",
        salience=3,
        confidence=0.8,
        evidence_times_s=[2.8],
    )
    windows = derive_speech_free_windows(
        Transcript(
            language="en",
            segments=[TranscriptSegment(text="speech", time_range=TimeRange(start_s=4, end_s=8))],
        ),
        media_duration_s=12,
    )

    schedule = select_safe_window(event, narration_duration_s=0.4, windows=windows)

    assert schedule is not None
    assert schedule.narration_range == TimeRange(start_s=3, end_s=3.4)
    assert schedule.source_window_id == "window-1"


def test_scheduler_refuses_windows_more_than_eight_seconds_after_event() -> None:
    event = VisualEvent(
        id="event-1",
        time_range=TimeRange(start_s=1, end_s=2),
        facts=["A person enters."],
        kazakh_description="Адам кіреді.",
        salience=4,
        confidence=0.9,
        evidence_times_s=[1.5],
    )
    windows = derive_speech_free_windows(
        Transcript(
            language="en",
            segments=[TranscriptSegment(text="speech", time_range=TimeRange(start_s=0, end_s=11))],
        ),
        media_duration_s=15,
    )

    assert select_safe_window(event, narration_duration_s=1, windows=windows) is None
