"""Unit tests for TimeSlot value object."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from app.domain.value_objects.time_slot import TimeSlot


def make_slot(start_offset_h: float, end_offset_h: float) -> TimeSlot:
    base = datetime.now(UTC)
    return TimeSlot(base + timedelta(hours=start_offset_h), base + timedelta(hours=end_offset_h))


class TestTimeSlot:
    def test_valid_slot_created(self):
        slot = make_slot(1, 2)
        assert slot.duration_minutes == 60

    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match="End time must be after"):
            make_slot(2, 1)

    def test_equal_start_end_raises(self):
        now = datetime.now(UTC)
        with pytest.raises(ValueError):
            TimeSlot(now, now)

    def test_exceeds_24_hours_raises(self):
        with pytest.raises(ValueError, match="cannot exceed 24 hours"):
            make_slot(0, 25)

    def test_overlapping_slots(self):
        a = make_slot(0, 2)
        b = make_slot(1, 3)
        assert a.overlaps(b)
        assert b.overlaps(a)

    def test_non_overlapping_slots(self):
        a = make_slot(0, 1)
        b = make_slot(1, 2)
        assert not a.overlaps(b)
        assert not b.overlaps(a)

    def test_adjacent_slots_do_not_overlap(self):
        a = make_slot(0, 1)
        b = make_slot(1, 2)
        assert not a.overlaps(b)
        assert a.is_adjacent(b)

    def test_slot_contains_inner(self):
        outer = make_slot(0, 4)
        inner = make_slot(1, 3)
        assert outer.contains(inner)
        assert not inner.contains(outer)

    def test_equality(self):
        base = datetime.now(UTC)
        a = TimeSlot(base + timedelta(hours=1), base + timedelta(hours=2))
        b = TimeSlot(base + timedelta(hours=1), base + timedelta(hours=2))
        assert a == b

    def test_ordering(self):
        a = make_slot(0, 1)
        b = make_slot(2, 3)
        assert a < b

    def test_duration_calculation(self):
        slot = make_slot(0, 1.5)
        assert slot.duration_minutes == 90
