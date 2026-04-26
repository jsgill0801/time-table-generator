"""
Data Service – fetching and preprocessing.

This module is the bridge between the database and the
scheduling engine. It fetches raw records, cleans them,
and builds the data structures that the scheduler expects.
"""

from collections import defaultdict
import json
import os
from datetime import datetime

from sqlalchemy.orm import Session

from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse

from backend.utils.helpers import (
    format_ltpc,
    build_batch_label,
    calculate_required_sessions,
    DAY_ORDER,
)


class DataService:
    """
    Central service for fetching data from the database and
    preprocessing it into clean structures for the scheduling engine.

    Usage:
        db = next(get_db())
        service = DataService(db)
        scheduling_input = service.get_scheduling_input()
    """

    def __init__(self, db_session: Session):
        self.session = db_session
        self._debug_log_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "debug-ecec21.log",
        )
        self._run_id = f"data_{int(datetime.now().timestamp() * 1000)}"

    # =================================================================
    #  FETCHERS – pull raw data from the database
    # =================================================================

    def fetch_courses(self) -> list[dict]:
        """
        Fetch all courses ordered by course code.

        Returns a list of dicts, each containing:
            course_id, course_code, course_name,
            lectures, tutorials, labs, credits, ltpc
        """
        courses = (
            self.session
            .query(Course)
            .order_by(Course.course_code)
            .all()
        )

        return [course.to_dict() for course in courses]

    def fetch_batches(self) -> list[dict]:
        """
        Fetch all batches ordered by program, semester, branch.

        Returns a list of dicts, each containing:
            batch_id, program, branch, semester, section, label
        """
        batches = (
            self.session
            .query(Batch)
            .order_by(Batch.program, Batch.semester, Batch.branch)
            .all()
        )

        return [batch.to_dict() for batch in batches]

    def fetch_faculties(self) -> list[dict]:
        """
        Fetch all faculty members ordered by faculty code.

        Returns a list of dicts, each containing:
            faculty_code, faculty_name, faculty_email, max_load
        """
        faculties = (
            self.session
            .query(Faculty)
            .order_by(Faculty.faculty_code)
            .all()
        )

        return [faculty.to_dict() for faculty in faculties]

    def fetch_classrooms(self) -> list[dict]:
        """
        Fetch all classrooms ordered by name.

        Returns a list of dicts, each containing:
            classroom_name, capacity
        """
        classrooms = (
            self.session
            .query(Classroom)
            .order_by(Classroom.classroom_name)
            .all()
        )

        return [room.to_dict() for room in classrooms]

    def fetch_slots(self) -> list[dict]:
        """
        Fetch all time slots, sorted by day of week then start time.

        Returns a list of dicts, each containing:
            slot_id, day_of_week, start_time, end_time, slot_name
        """
        slots = (
            self.session
            .query(Slot)
            .all()
        )

        # Convert to dicts first, then sort using our day ordering
        slot_dicts = [slot.to_dict() for slot in slots]

        slot_dicts.sort(
            key=lambda s: (
                DAY_ORDER.get(s["day_of_week"], 99),
                s["start_time"],
            )
        )

        return slot_dicts

    def fetch_batch_courses(self) -> list[dict]:
        """
        Fetch all batch-course mappings with joined course,
        batch, and category information.

        Returns a list of dicts with combined fields from
        all three tables plus the enrollment count.
        """
        results = (
            self.session
            .query(BatchCourse, Course, Batch, Category)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .join(Batch, BatchCourse.batch_id == Batch.batch_id)
            .outerjoin(Category, BatchCourse.category_id == Category.category_id)
            .order_by(Batch.program, Batch.semester, Course.course_code)
            .all()
        )

        batch_courses = []

        for bc, course, batch, category in results:
            batch_courses.append({
                "auto_id": bc.auto_id,
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "lectures": course.lectures,
                "tutorials": course.tutorials,
                "labs": course.labs,
                "credits": course.credits,
                "ltpc": format_ltpc(
                    course.lectures, course.tutorials,
                    course.labs, course.credits,
                ),
                "batch_id": batch.batch_id,
                "batch_label": batch.label,
                "category_name": category.category_name if category else None,
                "students_enrolled": bc.students_enrolled,
            })

        return batch_courses

    def fetch_faculty_courses(self) -> list[dict]:
        """
        Fetch all faculty-course mappings with joined
        faculty and course details.

        Returns a list of dicts combining fields from both tables.
        """
        results = (
            self.session
            .query(FacultyCourse, Faculty, Course)
            .join(Faculty, FacultyCourse.faculty_code == Faculty.faculty_code)
            .join(Course, FacultyCourse.course_id == Course.course_id)
            .order_by(Faculty.faculty_code, Course.course_code)
            .all()
        )

        faculty_courses = []

        for fc, faculty, course in results:
            faculty_courses.append({
                "auto_id": fc.auto_id,
                "faculty_code": faculty.faculty_code,
                "faculty_name": faculty.faculty_name,
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
            })

        return faculty_courses

    # =================================================================
    #  PREPROCESSORS – transform raw data for the scheduler
    # =================================================================

    def build_faculty_load_map(self) -> dict:
        """
        Build a lookup of each faculty's teaching load limit.

        Returns:
            {
                "PD": {"max_load": 12, "current_load": 0},
                "AV": {"max_load": 10, "current_load": 0},
                ...
            }

        The scheduler increments current_load as it assigns
        sessions and checks against max_load.
        """
        faculties = self.fetch_faculties()

        load_map = {}

        for f in faculties:
            load_map[f["faculty_code"]] = {
                "max_load": f["max_load"],
                "current_load": 0,
            }

        return load_map

    def build_room_capacity_index(self) -> dict:
        """
        Build a lookup of room capacities, sorted largest first.

        Returns:
            OrderedDict-like dict:
            {"LT-1": 200, "CEP211": 120, "CEP108": 60, ...}

        Sorting by descending capacity lets the scheduler
        quickly find the largest available room.
        """
        classrooms = self.fetch_classrooms()

        # Sort by capacity descending so largest rooms come first
        classrooms.sort(key=lambda r: r["capacity"], reverse=True)

        return {
            room["classroom_name"]: room["capacity"]
            for room in classrooms
        }

    def build_batch_lecture_demand(self) -> list[dict]:
        """
        Build the list of scheduling units (the "demand").

        Each unit represents one batch-course pair that needs
        a certain number of lecture sessions scheduled per week.

        For each batch-course, we look up which faculty teaches
        that course to include in the demand entry.

        Returns:
            [
                {
                    "batch_course_id": 1,
                    "course_code": "IT205",
                    "course_name": "Data Structures",
                    "batch_label": "BTech Sem-II (ICT + CS)",
                    "faculty_code": "AR2",
                    "lectures_required": 3,
                    "students_enrolled": 80,
                    "category": "Core",
                    "ltpc": "3-0-0-3",
                },
                ...
            ]
        """
        batch_courses = self.fetch_batch_courses()
        faculty_courses = self.fetch_faculty_courses()

        # Build a quick lookup: course_id -> list of faculty codes
        course_faculty_map = defaultdict(list)

        for fc in faculty_courses:
            course_faculty_map[fc["course_id"]].append(fc["faculty_code"])

        # Build the demand list
        demand = []
        grouped_by_course = defaultdict(list)
        for bc in batch_courses:
            grouped_by_course[bc["course_id"]].append(bc)

        for course_id, grouped in grouped_by_course.items():
            grouped_sorted = sorted(grouped, key=lambda x: x["batch_label"])
            course_total_sessions = calculate_required_sessions(
                grouped_sorted[0]["lectures"],
                grouped_sorted[0]["tutorials"],
                grouped_sorted[0]["labs"],
            )
            mapping_count = len(grouped_sorted)
            base = int(course_total_sessions // mapping_count) if mapping_count else 0
            remainder = int(course_total_sessions % mapping_count) if mapping_count else 0

            for idx, bc in enumerate(grouped_sorted):
                # Find faculty assigned to this course
                faculty_codes = course_faculty_map.get(bc["course_id"], [])

                # Use the first assigned faculty, or None if unassigned
                # (validation_service will catch unassigned courses later)
                faculty_code = faculty_codes[0] if faculty_codes else None

                lectures_required = base + (1 if idx < remainder else 0)

                # If multiple faculty teach jointly (e.g. "SS/VS"),
                # they'll be stored as a single faculty_code in the DB
                demand.append({
                    "batch_course_id": bc["auto_id"],
                    "course_code": bc["course_code"],
                    "course_name": bc["course_name"],
                    "batch_label": bc["batch_label"],
                    "faculty_code": faculty_code,
                    "lectures_required": lectures_required,
                    "students_enrolled": bc["students_enrolled"],
                    "category": bc["category_name"],
                    "ltpc": bc["ltpc"],
                })

        # region agent log
        try:
            sample = [
                {
                    "course_code": d["course_code"],
                    "batch_label": d["batch_label"],
                    "lectures_required": d["lectures_required"],
                    "ltpc": d["ltpc"],
                }
                for d in demand[:10]
            ]
            payload = {
                "sessionId": "ecec21",
                "runId": self._run_id,
                "hypothesisId": "H7",
                "location": "data_service.py:build_batch_lecture_demand",
                "message": "Built demand with required sessions",
                "data": {"demand_count": len(demand), "sample": sample},
                "timestamp": int(datetime.now().timestamp() * 1000),
            }
            with open(self._debug_log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception:
            pass
        # endregion

        return demand

    def build_slot_day_index(self) -> dict:
        """
        Group slots by day of week, ordered by start time.

        Returns:
            {
                "Monday":    ["MON-0800", "MON-0900", ...],
                "Tuesday":   ["TUE-0800", "TUE-0900", ...],
                "Wednesday": ["WED-0900", ...],
                ...
            }

        This structure lets the scheduler iterate through
        each day's slots in chronological order.
        """
        slots = self.fetch_slots()

        day_index = defaultdict(list)

        for slot in slots:
            day_index[slot["day_of_week"]].append(slot["slot_id"])

        # Sort the days in weekday order
        sorted_index = dict(
            sorted(
                day_index.items(),
                key=lambda item: DAY_ORDER.get(item[0], 99),
            )
        )

        return sorted_index

    def build_slot_lookup(self) -> dict:
        """
        Build a flat lookup from slot_id to full slot info.

        Returns:
            {
                "MON-0800": {
                    "slot_id": "MON-0800",
                    "day_of_week": "Monday",
                    "start_time": "08:00:00",
                    "end_time": "08:50:00",
                    "slot_name": "Slot-1",
                },
                ...
            }

        Useful for the scheduler to quickly look up slot
        details when assigning a session.
        """
        slots = self.fetch_slots()
        return {slot["slot_id"]: slot for slot in slots}

    # =================================================================
    #  MASTER METHOD – single entry point for the scheduler
    # =================================================================

    def get_scheduling_input(self) -> dict:
        """
        Fetch and preprocess all data needed by the scheduling engine.

        This is the single method the scheduler calls to get
        everything it needs in one clean package.

        Returns:
            {
                "demand":           [...],  # scheduling units
                "faculty_load":     {...},  # faculty load map
                "room_index":       {...},  # room capacities
                "slot_day_index":   {...},  # slots grouped by day
                "slot_lookup":      {...},  # slot_id -> full info
                "all_slots":        [...],  # raw slot list
                "all_rooms":        [...],  # raw room list
            }
        """
        return {
            "demand": self.build_batch_lecture_demand(),
            "faculty_load": self.build_faculty_load_map(),
            "room_index": self.build_room_capacity_index(),
            "slot_day_index": self.build_slot_day_index(),
            "slot_lookup": self.build_slot_lookup(),
            "all_slots": self.fetch_slots(),
            "all_rooms": self.fetch_classrooms(),
        }
