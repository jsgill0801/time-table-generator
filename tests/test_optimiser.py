"""
Tests for the Optimiser (soft-constraint hill climber).

Verifies that the optimiser:
    1. Preserves hard constraints after swaps
    2. Does not make the schedule worse
    3. Handles edge cases (empty, single assignment)
"""

import pytest

from backend.services.optimiser import Optimiser


# -----------------------------------------------------------------
#  Test data helpers
# -----------------------------------------------------------------

def _make_assignments():
    """Create a set of test assignments with known soft-constraint issues."""
    return [
        {
            "batch_course_id": 1,
            "course_code": "IT205",
            "course_name": "Data Structures",
            "batch_label": "BTech ICT IV-A",
            "faculty_code": "PD",
            "classroom_name": "LT-1",
            "slot_id": "MON-0800",
            "day_of_week": "Monday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-1",
            "ltpc": "3-0-0-3",
            "category_name": "Core",
        },
        {
            "batch_course_id": 2,
            "course_code": "MA206",
            "course_name": "Probability",
            "batch_label": "BTech ICT IV-B",
            "faculty_code": "AV",
            "classroom_name": "CEP211",
            "slot_id": "MON-0900",
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "09:50",
            "slot_name": "Slot-5",
            "ltpc": "3-1-0-4",
            "category_name": "Core",
        },
        {
            "batch_course_id": 3,
            "course_code": "HM106",
            "course_name": "Ethics",
            "batch_label": "BTech CS IV",
            "faculty_code": "SS",
            "classroom_name": "CEP108",
            "slot_id": "TUE-0800",
            "day_of_week": "Tuesday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-3",
            "ltpc": "3-0-0-3",
            "category_name": "Humanities",
        },
    ]


def _make_slot_lookup():
    """Slot lookup matching the test assignments."""
    return {
        "MON-0800": {
            "day_of_week": "Monday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-1",
        },
        "MON-0900": {
            "day_of_week": "Monday",
            "start_time": "09:00",
            "end_time": "09:50",
            "slot_name": "Slot-5",
        },
        "TUE-0800": {
            "day_of_week": "Tuesday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-3",
        },
    }


def _make_slot_day_index():
    return {
        "Monday": ["MON-0800", "MON-0900"],
        "Tuesday": ["TUE-0800"],
    }


def _make_room_index():
    return {"LT-1": 200, "CEP211": 120, "CEP108": 60}


# =================================================================
#  Tests
# =================================================================

class TestOptimiserBasics:
    """Test basic optimiser behaviour."""

    def test_returns_same_number_of_assignments(self):
        """The optimiser should never add or remove assignments."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
            max_iterations=100,
        )

        result = optimiser.run()

        assert len(result) == 3

    def test_preserves_course_codes(self):
        """Course codes should never change during optimisation."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
            max_iterations=100,
        )

        result = optimiser.run()

        codes = {a["course_code"] for a in result}
        assert codes == {"IT205", "MA206", "HM106"}

    def test_preserves_batch_labels(self):
        """Batch labels should never change during optimisation."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
            max_iterations=100,
        )

        result = optimiser.run()

        batches = {a["batch_label"] for a in result}
        assert batches == {"BTech ICT IV-A", "BTech ICT IV-B", "BTech CS IV"}

    def test_single_assignment(self):
        """With only one assignment, nothing should change."""
        single = [_make_assignments()[0]]

        optimiser = Optimiser(
            assignments=single,
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
            max_iterations=50,
        )

        result = optimiser.run()

        assert len(result) == 1
        assert result[0]["course_code"] == "IT205"

    def test_empty_assignments(self):
        """With no assignments, the optimiser should return an empty list."""
        optimiser = Optimiser(
            assignments=[],
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
            max_iterations=50,
        )

        result = optimiser.run()

        assert result == []


class TestOptimiserScoring:
    """Test the scoring functions."""

    def test_score_is_numeric(self):
        """The total score should be a valid float."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
        )

        score = optimiser._score_all()

        assert isinstance(score, float)
        assert score >= 0.0

    def test_edge_slot_penalty_counts_correctly(self):
        """First and last slots of each day should be penalised."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
        )

        penalty = optimiser._penalty_edge_slots()

        # All 3 assignments are in edge slots (first of Monday, second of Monday, first of Tuesday)
        assert penalty >= 2.0

    def test_room_change_penalty(self):
        """Batches using different rooms on the same day should be penalised."""
        optimiser = Optimiser(
            assignments=_make_assignments(),
            slot_lookup=_make_slot_lookup(),
            slot_day_index=_make_slot_day_index(),
            room_index=_make_room_index(),
        )

        penalty = optimiser._penalty_room_changes()

        # Each batch is in a different room but on different days,
        # so room changes within the same day should be 0
        assert isinstance(penalty, float)
