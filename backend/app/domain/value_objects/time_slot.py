from __future__ import annotations

from datetime import datetime, timedelta


class TimeSlot:
    def __init__(self, start: datetime, end: datetime) -> None:
        if end <= start:
            raise ValueError("End time must be after start time")
        if (end - start) > timedelta(hours=24):
            raise ValueError("Time slot cannot exceed 24 hours")
        self._start = start
        self._end = end

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self._end

    @property
    def duration_minutes(self) -> int:
        return int((self._end - self._start).total_seconds() / 60)

    def overlaps(self, other: "TimeSlot") -> bool:
        return self._start < other._end and self._end > other._start

    def contains(self, other: "TimeSlot") -> bool:
        return self._start <= other._start and self._end >= other._end

    def is_adjacent(self, other: "TimeSlot") -> bool:
        return self._end == other._start or other._end == self._start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return self._start == other._start and self._end == other._end

    def __hash__(self) -> int:
        return hash((self._start, self._end))

    def __repr__(self) -> str:
        return f"TimeSlot({self._start.isoformat()} - {self._end.isoformat()})"

    def __lt__(self, other: "TimeSlot") -> bool:
        return self._start < other._start
