"""
Scheduling Engine – hard-constraint satisfaction.

This is the core algorithm that assigns courses to (slot, room)
pairs while enforcing all hard constraints. It works as a greedy
constraint-satisfaction solver:

    For each demand entry (batch-course pair):
        For each lecture that needs scheduling:
            Scan all slots and rooms for a valid assignment.
            If found, record the assignment and move on.
            If not, log it as an unresolved conflict.

Hard constraints enforced:
    1. No faculty double-booking in the same slot
    2. Faculty must stay within their max weekly load
    3. No batch double-booking in the same slot
    4. No room double-booking in the same slot
    5. Room capacity >= students enrolled
    6. No two consecutive time slots for the same faculty
"""

from collections import defaultdict
import json
import os
from datetime import datetime

from backend.utils.helpers import DAY_ORDER


class Scheduler:
    """
    Greedy constraint-satisfaction scheduler.

    Usage:
        scheduler = Scheduler(scheduling_input)
        result = scheduler.run()
        # result["assignments"] -> list of placed sessions
        # result["conflicts"]   -> list of unresolved sessions
    """

    def __init__(self, scheduling_input: dict):
        """
        Args:
            scheduling_input: The dict returned by DataService.get_scheduling_input()
        """
        self.demand = scheduling_input["demand"]
        self.faculty_load = scheduling_input["faculty_load"]
        self.room_index = scheduling_input["room_index"]
        self.slot_day_index = scheduling_input["slot_day_index"]
        self.slot_lookup = scheduling_input["slot_lookup"]

        # Build a flat list of all slot IDs in chronological order
        self.all_slot_ids = []
        for day in sorted(self.slot_day_index.keys(),
                          key=lambda d: DAY_ORDER.get(d, 99)):
            self.all_slot_ids.extend(self.slot_day_index[day])

        # ---- Tracking structures (mutated during scheduling) ----

        # Which slots are occupied by each faculty
        # { faculty_code: set(slot_id, ...) }
        self.faculty_slots = defaultdict(set)

        # Which slots are occupied by each batch-course's batch
        # { batch_label: set(slot_id, ...) }
        self.batch_slots = defaultdict(set)

        # Which slots are occupied in each room
        # { classroom_name: set(slot_id, ...) }
        self.room_slots = defaultdict(set)

        # Track which (day, time_index) each faculty has been assigned to,
        # so we can detect consecutive slots
        # { faculty_code: { day_of_week: set(time_position_index) } }
        self.faculty_day_positions = defaultdict(lambda: defaultdict(set))

        # Track which days of the week each course has been scheduled on
        # { batch_course_id: set(day_of_week, ...) }
        self.course_days = defaultdict(set)

        # Build time-position index for consecutive-slot detection
        # Maps slot_id -> (day_of_week, position_in_day)
        self.slot_position = {}
        for day, slot_ids in self.slot_day_index.items():
            for pos, sid in enumerate(slot_ids):
                self.slot_position[sid] = (day, pos)

        # Results
        self.assignments = []
        self.conflicts = []
        self._debug_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "debug-ecec21.log",
        )
        self._run_id = f"scheduler_{int(datetime.now().timestamp() * 1000)}"

        # Generate a random priority for each slot to distribute them randomly across slots of the same day
        import random
        self.slot_random_priority = {sid: random.random() for sid in self.all_slot_ids}  # nosec B311

    def run(self) -> dict:
        """
        Run the scheduling algorithm.

        Returns a dict with:
            - assignments: list of successfully placed sessions
            - conflicts: list of sessions that could not be placed
            - stats: summary counts
        """
        for entry in self.demand:
            lectures_needed = entry["lectures_required"]
            placed_for_entry = 0

            for lecture_num in range(lectures_needed):
                placed = self._try_place_lecture(entry, lecture_num + 1)

                if not placed:
                    self.conflicts.append({
                        "course_code": entry["course_code"],
                        "course_name": entry["course_name"],
                        "batch_label": entry["batch_label"],
                        "faculty_code": entry["faculty_code"],
                        "lecture_number": lecture_num + 1,
                        "reason": self._diagnose_failure(entry),
                    })
                else:
                    placed_for_entry += 1

            pass

        return {
            "assignments": self.assignments,
            "conflicts": self.conflicts,
            "stats": {
                "total_demand": sum(e["lectures_required"] for e in self.demand),
                "placed": len(self.assignments),
                "unresolved": len(self.conflicts),
            },
        }

    def _try_place_lecture(self, entry: dict, lecture_num: int) -> bool:
        """
        Try to find a valid (slot, room) pair for one lecture session.

        Iterates through all slots, sorted dynamically to spread lectures evenly across the week,
        and picks the first combination that passes all constraints.

        Returns True if placed successfully, False otherwise.
        """
        faculty_code = entry["faculty_code"]
        batch_label = entry["batch_label"]
        students = entry["students_enrolled"]

        # Calculate current daily load to spread lectures evenly
        global_day_counts = defaultdict(int)
        batch_day_counts = defaultdict(int)
        for a in self.assignments:
            global_day_counts[a["day_of_week"]] += 1
            if a["batch_label"] == batch_label:
                batch_day_counts[a["day_of_week"]] += 1

        # Sort slots dynamically: prioritize days with fewer assignments for this batch,
        # then globally less busy days, and finally randomize within the same day.
        sorted_slots = sorted(
            self.all_slot_ids,
            key=lambda sid: (
                batch_day_counts[self.slot_lookup[sid]["day_of_week"]],
                global_day_counts[self.slot_lookup[sid]["day_of_week"]],
                self.slot_random_priority[sid]
            )
        )

        for slot_id in sorted_slots:
            slot_info = self.slot_lookup.get(slot_id)
            if not slot_info:
                continue

            # Skip free slots
            if slot_info.get("slot_name") == "Free-Slot":
                continue

            # Check faculty availability for this slot
            if not self._check_faculty_slot(faculty_code, slot_id):
                continue

            # Check batch availability for this slot
            if slot_id in self.batch_slots[batch_label]:
                continue

            # Check consecutive-slot constraint for faculty
            if not self._check_no_consecutive(faculty_code, slot_id):
                continue

            # Check if this course already has a lecture scheduled on this day
            day_of_week = slot_info["day_of_week"]
            if day_of_week in self.course_days[entry["batch_course_id"]]:
                continue

            # Try each room (they are sorted largest-first in room_index)
            for room_name, capacity in self.room_index.items():

                # Check room capacity
                if capacity < students:
                    continue

                # Check room availability for this slot
                if slot_id in self.room_slots[room_name]:
                    continue

                # All constraints pass — place the assignment
                self._record_assignment(entry, slot_id, slot_info, room_name)
                return True

        return False

    def _check_faculty_slot(self, faculty_code: str, slot_id: str) -> bool:
        """
        Check if the faculty is available in this slot.

        Checks:
            - Faculty is not already teaching in this slot
            - Faculty has not exceeded their max weekly load
        """
        if not faculty_code:
            return True  # no faculty assigned, skip faculty checks

        # Already teaching in this slot?
        if slot_id in self.faculty_slots[faculty_code]:
            return False

        # Exceeded max load?
        load_info = self.faculty_load.get(faculty_code)
        if load_info and load_info["current_load"] >= load_info["max_load"]:
            return False

        return True

    def _check_no_consecutive(self, faculty_code: str, slot_id: str) -> bool:
        """
        Check that assigning this slot would not create two
        consecutive time slots for the faculty on the same day.

        Two slots are consecutive if their position indices
        differ by exactly 1 on the same day.
        """
        if not faculty_code:
            return True

        if slot_id not in self.slot_position:
            return True

        day, pos = self.slot_position[slot_id]
        faculty_positions = self.faculty_day_positions[faculty_code][day]

        # Check if the adjacent positions are already occupied
        if (pos - 1) in faculty_positions or (pos + 1) in faculty_positions:
            return False

        return True

    def _record_assignment(self, entry: dict, slot_id: str,
                           slot_info: dict, room_name: str):
        """
        Record a successful assignment and update all tracking structures.
        """
        faculty_code = entry["faculty_code"]
        batch_label = entry["batch_label"]

        # Build the assignment record
        assignment = {
            "batch_course_id": entry["batch_course_id"],
            "faculty_code": faculty_code,
            "classroom_name": room_name,
            "slot_id": slot_id,
            "day_of_week": slot_info["day_of_week"],
            "start_time": slot_info["start_time"],
            "end_time": slot_info["end_time"],
            "slot_name": slot_info.get("slot_name"),
            "course_code": entry["course_code"],
            "course_name": entry["course_name"],
            "ltpc": entry["ltpc"],
            "category_name": entry["category"],
            "batch_label": batch_label,
        }

        self.assignments.append(assignment)

        # Update tracking structures
        if faculty_code:
            self.faculty_slots[faculty_code].add(slot_id)

            # Update load counter
            if faculty_code in self.faculty_load:
                self.faculty_load[faculty_code]["current_load"] += 1

            # Update position tracking for consecutive-slot detection
            if slot_id in self.slot_position:
                day, pos = self.slot_position[slot_id]
                self.faculty_day_positions[faculty_code][day].add(pos)

        self.batch_slots[batch_label].add(slot_id)
        self.room_slots[room_name].add(slot_id)
        self.course_days[entry["batch_course_id"]].add(slot_info["day_of_week"])

    def _diagnose_failure(self, entry: dict) -> str:
        """
        Provide a human-readable reason why a lecture could not be placed.

        Checks each constraint individually to identify the bottleneck.
        """
        faculty_code = entry["faculty_code"]
        batch_label = entry["batch_label"]
        students = entry["students_enrolled"]

        # Check if faculty is fully booked
        if faculty_code:
            load_info = self.faculty_load.get(faculty_code)
            if load_info and load_info["current_load"] >= load_info["max_load"]:
                return (
                    f"Faculty '{faculty_code}' has reached their maximum "
                    f"weekly load of {load_info['max_load']} lectures."
                )

        # Check if the batch has no free slots left
        used_batch_slots = len(self.batch_slots[batch_label])
        total_available = len([
            s for s in self.all_slot_ids
            if self.slot_lookup.get(s, {}).get("slot_name") != "Free-Slot"
        ])
        if used_batch_slots >= total_available:
            return f"Batch '{batch_label}' has no free slots remaining."

        # Check if there are rooms big enough
        suitable_rooms = [
            name for name, cap in self.room_index.items()
            if cap >= students
        ]
        if not suitable_rooms:
            return (
                f"No classroom has capacity >= {students} students. "
                f"Largest room holds {max(self.room_index.values())} students."
            )

        # Generic fallback
        return (
            "No valid (slot, room) combination found. "
            "All candidate slots are blocked by faculty, batch, "
            "room conflicts, or the consecutive-lecture constraint."
        )
