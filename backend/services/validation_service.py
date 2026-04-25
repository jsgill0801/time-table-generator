"""
Validation Service – pre-generation integrity checks.

Before the scheduling engine runs, this module performs a
full integrity check across all loaded datasets. If any
critical issue is found, generation is halted and a detailed
report of every problem is returned.

This catches issues like:
    - Courses with no assigned faculty
    - Rooms too small for any batch's enrollment
    - Not enough time slots for the total lecture demand
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse
from backend.models.category import Category

from backend.utils.errors import ValidationError
from backend.utils.helpers import format_ltpc


class ValidationService:
    """
    Runs a series of integrity checks on the data before
    the timetable generation engine is allowed to start.

    Usage:
        validator = ValidationService(db_session)
        errors = validator.run_all_checks()

        if errors:
            # halt generation, return errors to the user
            raise ValidationError(errors)
    """

    def __init__(self, db_session: Session):
        self.session = db_session

    def run_all_checks(self) -> list[str]:
        """
        Run every validation check and collect all errors.

        Returns a list of human-readable error strings.
        An empty list means all checks passed.
        """
        errors = []

        errors.extend(self.check_courses_have_faculty())
        errors.extend(self.check_room_capacity())
        errors.extend(self.check_slot_supply())
        errors.extend(self.check_faculty_load_feasibility())
        errors.extend(self.check_batch_courses_exist())
        errors.extend(self.check_slot_overlaps())
        errors.extend(self.check_batch_slot_feasibility())
        errors.extend(self.check_duplicate_batch_courses())

        return errors

    # -----------------------------------------------------------------
    #  Check 1: Every course assigned to a batch must have a faculty
    # -----------------------------------------------------------------

    def check_courses_have_faculty(self) -> list[str]:
        """
        Verify that every course in the batch_course table
        has at least one faculty member assigned to teach it.
        """
        errors = []

        # Get all course IDs that have a batch-course mapping
        batch_courses = self.session.query(BatchCourse).all()
        assigned_course_ids = {bc.course_id for bc in batch_courses}

        # Get all course IDs that have a faculty-course mapping
        faculty_courses = self.session.query(FacultyCourse).all()
        faculty_assigned_ids = {fc.course_id for fc in faculty_courses}

        # Find courses that are assigned to batches but have no faculty
        missing = assigned_course_ids - faculty_assigned_ids

        for course_id in missing:
            course = self.session.get(Course, course_id)

            if course:
                errors.append(
                    f"Course '{course.course_code} – {course.course_name}' "
                    f"is assigned to one or more batches but has no faculty. "
                    f"Please assign at least one faculty member."
                )

        return errors

    # -----------------------------------------------------------------
    #  Check 2: Room capacity must fit the enrolled students
    # -----------------------------------------------------------------

    def check_room_capacity(self) -> list[str]:
        """
        Verify that for every batch-course, there exists at least
        one classroom with capacity >= students_enrolled.

        If the largest room is still too small, the scheduler
        will never find a valid assignment.
        """
        errors = []

        # Find the largest available room
        max_room = (
            self.session
            .query(Classroom)
            .order_by(Classroom.capacity.desc())
            .first()
        )

        if not max_room:
            errors.append("No classrooms found. Please add at least one classroom.")
            return errors

        max_capacity = max_room.capacity

        # Check each batch-course enrollment against the max room
        batch_courses = (
            self.session
            .query(BatchCourse, Course, Batch)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .join(Batch, BatchCourse.batch_id == Batch.batch_id)
            .all()
        )

        for bc, course, batch in batch_courses:
            if bc.students_enrolled > max_capacity:
                errors.append(
                    f"Course '{course.course_code} – {course.course_name}' "
                    f"for batch '{batch.label}' has {bc.students_enrolled} students, "
                    f"but the largest room '{max_room.classroom_name}' "
                    f"only holds {max_capacity}. No valid room assignment is possible."
                )

        return errors

    # -----------------------------------------------------------------
    #  Check 3: Enough time slots for the total lecture demand
    # -----------------------------------------------------------------

    def check_slot_supply(self) -> list[str]:
        """
        Verify that the total number of available slot-room pairs
        is sufficient for the total number of lectures demanded.

        This is a basic feasibility check — if total_demand > total_slots × total_rooms,
        a conflict-free solution is mathematically impossible.
        """
        errors = []

        # Count total available slots (excluding Free-Slots)
        total_slots = (
            self.session
            .query(Slot)
            .filter(Slot.slot_name != "Free-Slot")
            .count()
        )

        if total_slots == 0:
            errors.append("No time slots found. Please add at least one slot.")
            return errors

        # Count total rooms
        total_rooms = self.session.query(Classroom).count()

        if total_rooms == 0:
            errors.append("No classrooms found. Please add at least one classroom.")
            return errors

        # Total capacity = slots × rooms (each slot-room pair holds one session)
        total_capacity = total_slots * total_rooms

        # Count total lecture demand across all batch-courses
        batch_courses = (
            self.session
            .query(BatchCourse, Course)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .all()
        )

        total_demand = sum(course.lectures for _, course in batch_courses)

        if total_demand > total_capacity:
            errors.append(
                f"Total lecture demand ({total_demand} sessions) exceeds "
                f"total scheduling capacity ({total_slots} slots × {total_rooms} rooms "
                f"= {total_capacity} session slots). "
                f"A conflict-free timetable is not possible. "
                f"Consider adding more slots or classrooms."
            )

        return errors

    # -----------------------------------------------------------------
    #  Check 4: Faculty load is feasible
    # -----------------------------------------------------------------

    def check_faculty_load_feasibility(self) -> list[str]:
        """
        Verify that no faculty member is assigned more lectures
        per week than their max_load allows.

        Counts the total lectures across all courses assigned
        to each faculty and compares with their max_load.
        """
        errors = []

        # For each faculty, sum up the lectures from all their assigned courses
        faculty_courses = (
            self.session
            .query(FacultyCourse, Course, Faculty)
            .join(Course, FacultyCourse.course_id == Course.course_id)
            .join(Faculty, FacultyCourse.faculty_code == Faculty.faculty_code)
            .all()
        )

        # Aggregate lectures per faculty
        faculty_load = defaultdict(lambda: {"name": "", "max": 0, "assigned": 0})

        for fc, course, faculty in faculty_courses:
            entry = faculty_load[faculty.faculty_code]
            entry["name"] = faculty.faculty_name
            entry["max"] = faculty.max_load

            # Count how many batches have this course (each batch = separate lectures)
            batch_count = (
                self.session
                .query(BatchCourse)
                .filter(BatchCourse.course_id == course.course_id)
                .count()
            )

            entry["assigned"] += course.lectures * batch_count

        for code, info in faculty_load.items():
            if info["assigned"] > info["max"]:
                errors.append(
                    f"Faculty '{code} – {info['name']}' has a max load of "
                    f"{info['max']} lectures/week but is assigned "
                    f"{info['assigned']} lectures. "
                    f"Reduce their course assignments or increase their max load."
                )

        return errors

    # -----------------------------------------------------------------
    #  Check 5: Basic data existence checks
    # -----------------------------------------------------------------

    def check_batch_courses_exist(self) -> list[str]:
        """
        Verify that the database has enough data to even attempt
        generation: at least one batch-course, one slot, one room.
        """
        errors = []

        if self.session.query(BatchCourse).count() == 0:
            errors.append(
                "No batch-course mappings found. "
                "Please assign courses to batches before generating."
            )

        if self.session.query(Slot).count() == 0:
            errors.append(
                "No time slots found. "
                "Please define the weekly slot grid before generating."
            )

        if self.session.query(Classroom).count() == 0:
            errors.append(
                "No classrooms found. "
                "Please add classroom data before generating."
            )

        return errors

    # -----------------------------------------------------------------
    #  Check 6: Detect overlapping time slots on the same day
    # -----------------------------------------------------------------

    def check_slot_overlaps(self) -> list[str]:
        """
        Verify that no two time slots on the same day have
        overlapping time ranges.

        Overlapping slots would mean the scheduler could
        accidentally double-book a batch or faculty even
        though it thinks they are in different slots.
        """
        errors = []

        slots = self.session.query(Slot).all()

        # Group slots by day
        day_slots = defaultdict(list)
        for slot in slots:
            day_slots[slot.day_of_week].append(slot)

        for day, slot_list in day_slots.items():
            # Sort by start time
            slot_list.sort(key=lambda s: s.start_time)

            for i in range(len(slot_list) - 1):
                current = slot_list[i]
                next_slot = slot_list[i + 1]

                # Overlap: current ends after next starts
                if current.end_time > next_slot.start_time:
                    errors.append(
                        f"Slot '{current.slot_id}' ({current.start_time}-{current.end_time}) "
                        f"overlaps with '{next_slot.slot_id}' ({next_slot.start_time}-{next_slot.end_time}) "
                        f"on {day}. Fix the slot times to avoid conflicts."
                    )

        return errors

    # -----------------------------------------------------------------
    #  Check 7: Each batch has enough non-free slots for its demand
    # -----------------------------------------------------------------

    def check_batch_slot_feasibility(self) -> list[str]:
        """
        Verify that each batch's total lecture demand does not
        exceed the number of available (non-free) time slots.

        Unlike check_slot_supply which is global, this catches
        cases where one specific batch has too many courses.
        """
        errors = []

        # Count non-free slots
        available_slots = (
            self.session
            .query(Slot)
            .filter(Slot.slot_name != "Free-Slot")
            .count()
        )

        if available_slots == 0:
            return errors  # already caught by check 5

        # Calculate per-batch demand
        batch_courses = (
            self.session
            .query(BatchCourse, Course, Batch)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .join(Batch, BatchCourse.batch_id == Batch.batch_id)
            .all()
        )

        batch_demand = defaultdict(int)
        for bc, course, batch in batch_courses:
            batch_demand[batch.label] += course.lectures

        for batch_label, demand in batch_demand.items():
            if demand > available_slots:
                errors.append(
                    f"Batch '{batch_label}' requires {demand} lecture sessions "
                    f"but only {available_slots} non-free slots are available. "
                    f"This batch cannot be fully scheduled."
                )

        return errors

    # -----------------------------------------------------------------
    #  Check 8: No duplicate batch-course assignments
    # -----------------------------------------------------------------

    def check_duplicate_batch_courses(self) -> list[str]:
        """
        Verify that no course is assigned to the same batch twice.

        While the database has a unique constraint, this check
        provides a clearer error message before the DB rejects it.
        """
        errors = []

        batch_courses = (
            self.session
            .query(BatchCourse, Course, Batch)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .join(Batch, BatchCourse.batch_id == Batch.batch_id)
            .all()
        )

        seen = set()
        for bc, course, batch in batch_courses:
            key = (course.course_code, batch.label)

            if key in seen:
                errors.append(
                    f"Course '{course.course_code}' is assigned to "
                    f"batch '{batch.label}' more than once. "
                    f"Remove the duplicate mapping."
                )

            seen.add(key)

        return errors
