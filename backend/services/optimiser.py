"""
Soft-constraint optimizer – hill-climbing improvement.

After the hard-constraint scheduler produces a feasible timetable,
this module tries to improve it by optimising for soft constraints.

Approach:
    1. Score the current schedule against all soft objectives.
    2. Randomly select two assignments and attempt a slot/room swap.
    3. Verify the swap still satisfies all hard constraints.
    4. If the swap improves the total score, keep it; otherwise revert.
    5. Repeat for a fixed number of iterations.

Soft constraints (each has a weight):
    1. Minimise faculty idle gaps between lectures on the same day
    2. Avoid scheduling in the first or last slot of the day
    3. Distribute a course's lectures evenly across weekdays
    4. Minimise room changes for the same batch on the same day
"""

import random
from collections import defaultdict

from backend.utils.helpers import DAY_ORDER


# -----------------------------------------------------------------
#  Scoring weights – higher = more important
# -----------------------------------------------------------------
WEIGHTS = {
    "faculty_idle_gaps": 3.0,
    "edge_slots": 1.0,
    "day_spread": 2.0,
    "room_changes": 1.5,
    "category_slot_alignment": 1.5,
}

# Default number of improvement attempts
DEFAULT_MAX_ITERATIONS = 2000


class Optimiser:
    """
    Hill-climbing optimizer for soft constraints.

    Usage:
        optimiser = Optimiser(assignments, slot_lookup, slot_day_index, room_index)
        improved = optimiser.run()
    """

    def __init__(self, assignments: list[dict], slot_lookup: dict,
                 slot_day_index: dict, room_index: dict,
                 max_iterations: int = DEFAULT_MAX_ITERATIONS):
        """
        Args:
            assignments:    List of assignment dicts from the Scheduler.
            slot_lookup:    { slot_id: {day_of_week, start_time, ...} }
            slot_day_index: { day_of_week: [slot_id, ...] }
            room_index:     { classroom_name: capacity }
            max_iterations: Number of swap attempts to try.
        """
        self.assignments = [a.copy() for a in assignments]  # work on a copy
        self.slot_lookup = slot_lookup
        self.slot_day_index = slot_day_index
        self.room_index = room_index
        self.max_iterations = max_iterations

        # Build a flat list of all non-free slot IDs
        self.valid_slot_ids = [
            sid for sid, info in slot_lookup.items()
            if info.get("slot_name") != "Free-Slot"
        ]

        # Identify edge slots (first and last of each day)
        self.edge_slots = set()
        for day, slot_ids in slot_day_index.items():
            non_free = [
                s for s in slot_ids
                if slot_lookup.get(s, {}).get("slot_name") != "Free-Slot"
            ]
            if non_free:
                self.edge_slots.add(non_free[0])
                self.edge_slots.add(non_free[-1])

        # Build position index for gap calculation
        self.slot_position = {}
        for day, slot_ids in slot_day_index.items():
            for pos, sid in enumerate(slot_ids):
                self.slot_position[sid] = (day, pos)

    def run(self) -> list[dict]:
        """
        Run the hill-climbing optimizer.

        Returns the improved list of assignments.
        """
        if len(self.assignments) < 2:
            return self.assignments

        current_score = self._score_all()
        improvements = 0

        for _ in range(self.max_iterations):
            # Pick two random assignments to try swapping
            i, j = random.sample(range(len(self.assignments)), 2)
            a1 = self.assignments[i]
            a2 = self.assignments[j]

            # Try swapping their slot + room assignments
            if not self._can_swap(a1, a2):
                continue

            # Perform the swap
            self._swap(a1, a2)

            # Score the new arrangement
            new_score = self._score_all()

            if new_score < current_score:
                # Improvement found, keep it
                current_score = new_score
                improvements += 1
            else:
                # No improvement, revert
                self._swap(a1, a2)

        return self.assignments

    # =================================================================
    #  SWAP LOGIC
    # =================================================================

    def _can_swap(self, a1: dict, a2: dict) -> bool:
        """
        Check whether swapping the slots of a1 and a2
        would violate any hard constraints.

        We only swap slots (not rooms) to keep room capacity valid.
        """
        # Don't swap if same batch (batch would be double-booked)
        if a1["batch_label"] == a2["batch_label"]:
            return False

        # Don't swap if same faculty (faculty would be double-booked)
        if (a1["faculty_code"] and a2["faculty_code"]
                and a1["faculty_code"] == a2["faculty_code"]):
            return False

        # Check room capacity after swap
        slot1 = a1["slot_id"]
        slot2 = a2["slot_id"]

        # If they're in the same slot, no point swapping
        if slot1 == slot2:
            return False

        # Check that the new slot doesn't conflict with other assignments
        # for the same batch or faculty (excluding each other)
        idx_a1 = self.assignments.index(a1)
        idx_a2 = self.assignments.index(a2)

        for idx, a in enumerate(self.assignments):
            if idx == idx_a1 or idx == idx_a2:
                continue

            # After swap: a1 is in slot2, a2 is in slot1
            # Check a1's batch and faculty against slot2
            if a["slot_id"] == slot2:
                if a["batch_label"] == a1["batch_label"]:
                    return False
                if (a1["faculty_code"] and a["faculty_code"]
                        and a["faculty_code"] == a1["faculty_code"]):
                    return False
                if a["classroom_name"] == a1["classroom_name"]:
                    return False

            # Check a2's batch and faculty against slot1
            if a["slot_id"] == slot1:
                if a["batch_label"] == a2["batch_label"]:
                    return False
                if (a2["faculty_code"] and a["faculty_code"]
                        and a["faculty_code"] == a2["faculty_code"]):
                    return False
                if a["classroom_name"] == a2["classroom_name"]:
                    return False

        # Keep hard constraint: no consecutive lectures for same faculty.
        if not self._check_no_consecutive_after_swap(a1, a2, slot2):
            return False
        if not self._check_no_consecutive_after_swap(a2, a1, slot1):
            return False

        return True

    def _check_no_consecutive_after_swap(self, target: dict, other: dict, new_slot_id: str) -> bool:
        faculty_code = target.get("faculty_code")
        if not faculty_code:
            return True
        if new_slot_id not in self.slot_position:
            return True

        day, pos = self.slot_position[new_slot_id]
        occupied_positions = set()

        for a in self.assignments:
            if a is target:
                continue
            slot_id = new_slot_id if a is other else a["slot_id"]
            if a.get("faculty_code") != faculty_code:
                continue
            if slot_id not in self.slot_position:
                continue
            s_day, s_pos = self.slot_position[slot_id]
            if s_day == day:
                occupied_positions.add(s_pos)

        return (pos - 1) not in occupied_positions and (pos + 1) not in occupied_positions

    def _swap(self, a1: dict, a2: dict):
        """Swap the slot assignments between two entries."""
        # Swap slot-related fields
        for field in ["slot_id", "day_of_week", "start_time", "end_time", "slot_name"]:
            a1[field], a2[field] = a2[field], a1[field]

    # =================================================================
    #  SCORING – lower is better
    # =================================================================

    def _score_all(self) -> float:
        """
        Calculate the total penalty score across all soft constraints.
        Lower score = better schedule.
        """
        score = 0.0

        score += WEIGHTS["faculty_idle_gaps"] * self._penalty_faculty_gaps()
        score += WEIGHTS["edge_slots"] * self._penalty_edge_slots()
        score += WEIGHTS["day_spread"] * self._penalty_day_spread()
        score += WEIGHTS["room_changes"] * self._penalty_room_changes()
        score += WEIGHTS["category_slot_alignment"] * self._penalty_category_slot_alignment()

        return score

    def _penalty_faculty_gaps(self) -> float:
        """
        Penalise idle gaps in a faculty's daily schedule.

        If a faculty teaches in positions 0 and 3 on Monday (skipping 1, 2),
        that's a gap of 2 idle slots. We want to minimise this.
        """
        # Group assignments by faculty and day
        faculty_days = defaultdict(lambda: defaultdict(list))

        for a in self.assignments:
            fc = a.get("faculty_code")
            if not fc:
                continue
            slot_id = a["slot_id"]
            if slot_id in self.slot_position:
                day, pos = self.slot_position[slot_id]
                faculty_days[fc][day].append(pos)

        total_gaps = 0

        for fc, days in faculty_days.items():
            for day, positions in days.items():
                if len(positions) < 2:
                    continue
                positions.sort()
                # Gap = difference between max and min positions
                # minus the number of lectures (the non-gap portion)
                span = positions[-1] - positions[0]
                gap = span - (len(positions) - 1)
                total_gaps += gap

        return float(total_gaps)

    def _penalty_edge_slots(self) -> float:
        """
        Penalise assignments in the first or last slot of each day.
        """
        count = sum(
            1 for a in self.assignments
            if a["slot_id"] in self.edge_slots
        )
        return float(count)

    def _penalty_day_spread(self) -> float:
        """
        Penalise uneven distribution of a course's lectures across days.

        Ideally, a course with 3 lectures/week should be spread
        across 3 different days, not clustered on 1 or 2 days.
        """
        # Group assignments by (batch_label, course_code)
        course_days = defaultdict(lambda: defaultdict(int))

        for a in self.assignments:
            key = (a["batch_label"], a["course_code"])
            course_days[key][a["day_of_week"]] += 1

        penalty = 0.0

        for key, day_counts in course_days.items():
            # Penalty for multiple lectures on the same day
            for day, count in day_counts.items():
                if count > 1:
                    penalty += (count - 1) * 2.0

        return penalty

    def _penalty_room_changes(self) -> float:
        """
        Penalise a batch having to switch rooms during the same day.
        """
        # Group by (batch_label, day) and collect rooms used
        batch_day_rooms = defaultdict(set)

        for a in self.assignments:
            key = (a["batch_label"], a["day_of_week"])
            batch_day_rooms[key].add(a["classroom_name"])

        # Each unique room beyond the first is a room change
        total_changes = sum(
            len(rooms) - 1
            for rooms in batch_day_rooms.values()
            if len(rooms) > 1
        )

        return float(total_changes)

    def _penalty_category_slot_alignment(self) -> float:
        """
        Penalise categories spread across too many distinct slot IDs.
        Lower values push same-category classes toward recurring slots.
        """
        category_slots = defaultdict(set)
        for a in self.assignments:
            category = (a.get("category_name") or "").strip()
            if not category:
                continue
            category_slots[category].add(a["slot_id"])

        return float(sum(max(len(slots) - 1, 0) for slots in category_slots.values()))
