"""
Tests for the Scheduler (hard-constraint engine).

Uses synthetic scheduling_input data to test constraint
enforcement without needing a database connection.
"""

import pytest

from backend.services.scheduler import Scheduler


# -----------------------------------------------------------------
#  Helpers: build minimal scheduling input
# -----------------------------------------------------------------

def _build_input(demand, faculty_load, room_index, slot_day_index, slot_lookup):
    """Construct a scheduling_input dict from parts."""
    return {
        "demand": demand,
        "faculty_load": faculty_load,
        "room_index": room_index,
        "slot_day_index": slot_day_index,
        "slot_lookup": slot_lookup,
        "all_slots": list(slot_lookup.values()),
        "all_rooms": [
            {"classroom_name": k, "capacity": v}
            for k, v in room_index.items()
        ],
    }


def _make_slot_lookup():
    """Create a standard 4-slot lookup for testing (spread across 3 days)."""
    return {
        "MON-0800": {
            "slot_id": "MON-0800",
            "day_of_week": "Monday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-1",
        },
        "MON-1000": {
            "slot_id": "MON-1000",
            "day_of_week": "Monday",
            "start_time": "10:00",
            "end_time": "10:50",
            "slot_name": "Slot-4",
        },
        "TUE-0800": {
            "slot_id": "TUE-0800",
            "day_of_week": "Tuesday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-3",
        },
        "WED-0800": {
            "slot_id": "WED-0800",
            "day_of_week": "Wednesday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-6",
        },
    }


def _make_slot_day_index():
    """Matching day index for the 4-slot lookup."""
    return {
        "Monday": ["MON-0800", "MON-1000"],
        "Tuesday": ["TUE-0800"],
        "Wednesday": ["WED-0800"],
    }


# =================================================================
#  Basic scheduling tests
# =================================================================

class TestBasicScheduling:
    """Test that the scheduler places lectures correctly."""

    def test_single_course_single_lecture(self):
        """One course, one lecture, one room, one slot — should place it."""
        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "Data Structures",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 1,
                "students_enrolled": 50,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 1
        assert result["stats"]["unresolved"] == 0
        assert result["assignments"][0]["course_code"] == "IT205"
        assert result["assignments"][0]["classroom_name"] == "LT-1"

    def test_multiple_lectures_placed(self):
        """A course with 3 lectures should be placed in 3 different slots."""
        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "Data Structures",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 3,
                "students_enrolled": 50,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 3
        assert result["stats"]["unresolved"] == 0

        # All assignments should have different slot_ids
        slot_ids = {a["slot_id"] for a in result["assignments"]}
        assert len(slot_ids) == 3

    def test_empty_demand(self):
        """No demand should produce no assignments and no conflicts."""
        scheduling_input = _build_input(
            demand=[],
            faculty_load={},
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["total_demand"] == 0
        assert result["stats"]["placed"] == 0
        assert result["stats"]["unresolved"] == 0


# =================================================================
#  Constraint enforcement tests
# =================================================================

class TestConstraintEnforcement:
    """Test that hard constraints are enforced."""

    def test_no_faculty_double_booking(self):
        """
        Two courses taught by the same faculty should never
        be placed in the same slot.
        """
        scheduling_input = _build_input(
            demand=[
                {
                    "batch_course_id": 1,
                    "course_code": "IT205",
                    "course_name": "Data Structures",
                    "batch_label": "BTech ICT IV-A",
                    "faculty_code": "PD",
                    "lectures_required": 1,
                    "students_enrolled": 50,
                    "category": "Core",
                    "ltpc": "3-0-0-3",
                },
                {
                    "batch_course_id": 2,
                    "course_code": "HM106",
                    "course_name": "Ethics",
                    "batch_label": "BTech ICT IV-B",
                    "faculty_code": "PD",
                    "lectures_required": 1,
                    "students_enrolled": 50,
                    "category": "Humanities",
                    "ltpc": "3-0-0-3",
                },
            ],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 2
        slots_used = [a["slot_id"] for a in result["assignments"]]
        assert slots_used[0] != slots_used[1]

    def test_no_batch_double_booking(self):
        """
        Two courses for the same batch should never be in the same slot.
        """
        scheduling_input = _build_input(
            demand=[
                {
                    "batch_course_id": 1,
                    "course_code": "IT205",
                    "course_name": "Data Structures",
                    "batch_label": "BTech ICT IV-A",
                    "faculty_code": "PD",
                    "lectures_required": 1,
                    "students_enrolled": 50,
                    "category": "Core",
                    "ltpc": "3-0-0-3",
                },
                {
                    "batch_course_id": 2,
                    "course_code": "MA206",
                    "course_name": "Probability",
                    "batch_label": "BTech ICT IV-A",
                    "faculty_code": "AV",
                    "lectures_required": 1,
                    "students_enrolled": 50,
                    "category": "Core",
                    "ltpc": "3-1-0-4",
                },
            ],
            faculty_load={
                "PD": {"max_load": 12, "current_load": 0},
                "AV": {"max_load": 10, "current_load": 0},
            },
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 2
        slots_used = [a["slot_id"] for a in result["assignments"]]
        assert slots_used[0] != slots_used[1]

    def test_room_capacity_respected(self):
        """
        A course with 100 students should not be placed in a
        room that only holds 60.
        """
        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "Data Structures",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 1,
                "students_enrolled": 100,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"SMALL": 60},  # too small
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 0
        assert result["stats"]["unresolved"] == 1
        assert "capacity" in result["conflicts"][0]["reason"].lower()

    def test_faculty_max_load_enforced(self):
        """
        A faculty with max_load=1 should not be scheduled more
        than 1 session even if demand is higher.
        """
        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "Data Structures",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 3,
                "students_enrolled": 50,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 1, "current_load": 0}},
            room_index={"LT-1": 200},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 1
        assert result["stats"]["unresolved"] == 2

    def test_free_slots_skipped(self):
        """The scheduler should not place anything in a Free-Slot."""
        slot_lookup = {
            "WED-0800": {
                "slot_id": "WED-0800",
                "day_of_week": "Wednesday",
                "start_time": "08:00",
                "end_time": "08:50",
                "slot_name": "Free-Slot",
            },
        }

        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "DS",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 1,
                "students_enrolled": 50,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"LT-1": 200},
            slot_day_index={"Wednesday": ["WED-0800"]},
            slot_lookup=slot_lookup,
        )

        result = Scheduler(scheduling_input).run()

        assert result["stats"]["placed"] == 0
        assert result["stats"]["unresolved"] == 1


# =================================================================
#  Conflict diagnosis tests
# =================================================================

class TestConflictDiagnosis:
    """Test that conflict reasons are informative."""

    def test_conflict_has_reason(self):
        """Every conflict should include a non-empty reason string."""
        scheduling_input = _build_input(
            demand=[{
                "batch_course_id": 1,
                "course_code": "IT205",
                "course_name": "DS",
                "batch_label": "BTech ICT IV-A",
                "faculty_code": "PD",
                "lectures_required": 1,
                "students_enrolled": 500,
                "category": "Core",
                "ltpc": "3-0-0-3",
            }],
            faculty_load={"PD": {"max_load": 12, "current_load": 0}},
            room_index={"SMALL": 30},
            slot_day_index=_make_slot_day_index(),
            slot_lookup=_make_slot_lookup(),
        )

        result = Scheduler(scheduling_input).run()

        assert len(result["conflicts"]) == 1
        assert result["conflicts"][0]["reason"] != ""
        assert len(result["conflicts"][0]["reason"]) > 10
