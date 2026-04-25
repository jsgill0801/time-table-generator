"""
Tests for the ValidationService.

Uses an in-memory SQLite database to test each validation
check independently with controlled test data.

Note: We set DATABASE_URL to SQLite before importing backend.db
      so the engine creation doesn't try to connect to PostgreSQL.
"""

import os
import pytest

# Override the DATABASE_URL before any backend imports
# so the engine uses SQLite instead of PostgreSQL
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db import Base
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse

from backend.services.validation_service import ValidationService

from datetime import time as dt_time


# -----------------------------------------------------------------
#  Test database fixtures
# -----------------------------------------------------------------

@pytest.fixture
def db_session():
    """Create a fresh in-memory SQLite database for each test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()


@pytest.fixture
def seeded_session(db_session):
    """
    Return a session pre-loaded with a minimal valid dataset.

    Contains: 1 course, 1 batch, 1 faculty, 1 room, 2 slots,
    1 batch-course mapping, 1 faculty-course mapping.
    """
    db = db_session

    # Course
    course = Course(
        course_code="IT205",
        course_name="Data Structures",
        lectures=3,
        tutorials=0,
        labs=0,
        credits=3.0,
    )
    db.add(course)
    db.flush()

    # Batch
    batch = Batch(program="BTech", branch="ICT", semester=4, section="A")
    db.add(batch)
    db.flush()

    # Faculty
    faculty = Faculty(
        faculty_code="PD",
        faculty_name="Prof. Divya",
        max_load=12,
    )
    db.add(faculty)
    db.flush()

    # Classroom
    room = Classroom(classroom_name="LT-1", capacity=200)
    db.add(room)

    # Slots – need at least 3 to match the course's 3 lectures/week
    db.add(Slot(
        slot_id="MON-0800", day_of_week="Monday",
        start_time=dt_time(8, 0), end_time=dt_time(8, 50),
        slot_name="Slot-1",
    ))
    db.add(Slot(
        slot_id="MON-0900", day_of_week="Monday",
        start_time=dt_time(9, 0), end_time=dt_time(9, 50),
        slot_name="Slot-5",
    ))
    db.add(Slot(
        slot_id="TUE-0800", day_of_week="Tuesday",
        start_time=dt_time(8, 0), end_time=dt_time(8, 50),
        slot_name="Slot-3",
    ))

    # Batch-Course mapping
    bc = BatchCourse(
        course_id=course.course_id,
        batch_id=batch.batch_id,
        students_enrolled=55,
    )
    db.add(bc)

    # Faculty-Course mapping
    fc = FacultyCourse(
        course_id=course.course_id,
        faculty_code="PD",
    )
    db.add(fc)

    db.commit()

    return db


# =================================================================
#  Test: All checks pass with valid data
# =================================================================

class TestAllChecksPassing:
    """Verify that a valid dataset produces zero errors."""

    def test_no_errors_with_valid_data(self, seeded_session):
        validator = ValidationService(seeded_session)
        errors = validator.run_all_checks()

        assert errors == []


# =================================================================
#  Test: Courses must have faculty
# =================================================================

class TestCoursesHaveFaculty:
    """Verify detection of courses without assigned faculty."""

    def test_detects_missing_faculty(self, seeded_session):
        db = seeded_session

        # Add a second course with no faculty assigned
        course2 = Course(
            course_code="MA206",
            course_name="Probability",
            lectures=3, tutorials=1, labs=0, credits=4.0,
        )
        db.add(course2)
        db.flush()

        # Assign it to a batch, but don't assign a faculty
        batch = db.query(Batch).first()
        db.add(BatchCourse(
            course_id=course2.course_id,
            batch_id=batch.batch_id,
            students_enrolled=50,
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_courses_have_faculty()

        assert len(errors) == 1
        assert "MA206" in errors[0]
        assert "no faculty" in errors[0].lower()


# =================================================================
#  Test: Room capacity check
# =================================================================

class TestRoomCapacity:
    """Verify detection of enrollment exceeding room capacity."""

    def test_detects_overcapacity(self, db_session):
        db = db_session

        # Only a small room
        db.add(Classroom(classroom_name="SMALL", capacity=30))

        course = Course(
            course_code="IT205", course_name="DS",
            lectures=3, tutorials=0, labs=0, credits=3.0,
        )
        db.add(course)
        db.flush()

        batch = Batch(program="BTech", branch="ICT", semester=4, section="A")
        db.add(batch)
        db.flush()

        # 100 students but max room is 30
        db.add(BatchCourse(
            course_id=course.course_id,
            batch_id=batch.batch_id,
            students_enrolled=100,
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_room_capacity()

        assert len(errors) == 1
        assert "100" in errors[0]
        assert "30" in errors[0]

    def test_passes_when_room_is_large_enough(self, seeded_session):
        validator = ValidationService(seeded_session)
        errors = validator.check_room_capacity()

        # LT-1 has capacity 200, enrollment is 55
        assert errors == []


# =================================================================
#  Test: Slot supply check
# =================================================================

class TestSlotSupply:
    """Verify detection of insufficient scheduling capacity."""

    def test_detects_insufficient_slots(self, db_session):
        db = db_session

        # Only 1 slot, 1 room = 1 session capacity
        db.add(Classroom(classroom_name="R1", capacity=100))
        db.add(Slot(
            slot_id="MON-0800", day_of_week="Monday",
            start_time=dt_time(8, 0), end_time=dt_time(8, 50),
            slot_name="Slot-1",
        ))

        # But demand is 3 lectures
        course = Course(
            course_code="IT205", course_name="DS",
            lectures=3, tutorials=0, labs=0, credits=3.0,
        )
        db.add(course)
        db.flush()

        batch = Batch(program="BTech", branch="ICT", semester=4, section="A")
        db.add(batch)
        db.flush()

        db.add(BatchCourse(
            course_id=course.course_id,
            batch_id=batch.batch_id,
            students_enrolled=50,
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_slot_supply()

        assert len(errors) == 1
        assert "exceeds" in errors[0].lower()


# =================================================================
#  Test: Faculty load feasibility
# =================================================================

class TestFacultyLoad:
    """Verify detection of faculty overloading."""

    def test_detects_overloaded_faculty(self, db_session):
        db = db_session

        # Faculty with max load of 2
        db.add(Faculty(
            faculty_code="PD", faculty_name="Prof. Divya", max_load=2,
        ))

        # Course with 3 lectures/week
        course = Course(
            course_code="IT205", course_name="DS",
            lectures=3, tutorials=0, labs=0, credits=3.0,
        )
        db.add(course)
        db.flush()

        batch = Batch(program="BTech", branch="ICT", semester=4, section="A")
        db.add(batch)
        db.flush()

        db.add(BatchCourse(
            course_id=course.course_id,
            batch_id=batch.batch_id,
            students_enrolled=50,
        ))
        db.add(FacultyCourse(
            course_id=course.course_id,
            faculty_code="PD",
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_faculty_load_feasibility()

        assert len(errors) == 1
        assert "PD" in errors[0]
        assert "max load" in errors[0].lower()


# =================================================================
#  Test: Batch-courses existence
# =================================================================

class TestDataExistence:
    """Verify detection of missing base data."""

    def test_no_batch_courses(self, db_session):
        validator = ValidationService(db_session)
        errors = validator.check_batch_courses_exist()

        assert len(errors) >= 1

    def test_passes_with_data(self, seeded_session):
        validator = ValidationService(seeded_session)
        errors = validator.check_batch_courses_exist()

        assert errors == []


# =================================================================
#  Test: Slot overlap detection (Check 6)
# =================================================================

class TestSlotOverlaps:
    """Verify detection of overlapping time slots."""

    def test_detects_overlap(self, db_session):
        db = db_session

        # Two slots that overlap: 8:00-9:00 and 8:30-9:30
        db.add(Slot(
            slot_id="MON-0800", day_of_week="Monday",
            start_time=dt_time(8, 0), end_time=dt_time(9, 0),
            slot_name="Slot-1",
        ))
        db.add(Slot(
            slot_id="MON-0830", day_of_week="Monday",
            start_time=dt_time(8, 30), end_time=dt_time(9, 30),
            slot_name="Slot-2",
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_slot_overlaps()

        assert len(errors) == 1
        assert "overlaps" in errors[0].lower()

    def test_no_overlap(self, seeded_session):
        validator = ValidationService(seeded_session)
        errors = validator.check_slot_overlaps()

        assert errors == []


# =================================================================
#  Test: Per-batch slot feasibility (Check 7)
# =================================================================

class TestBatchSlotFeasibility:
    """Verify detection of per-batch demand exceeding slot count."""

    def test_detects_overloaded_batch(self, db_session):
        db = db_session

        # 1 non-free slot available
        db.add(Slot(
            slot_id="MON-0800", day_of_week="Monday",
            start_time=dt_time(8, 0), end_time=dt_time(8, 50),
            slot_name="Slot-1",
        ))
        db.add(Classroom(classroom_name="R1", capacity=100))

        # Batch needs 3 lectures (but only 1 slot exists)
        course = Course(
            course_code="IT205", course_name="DS",
            lectures=3, tutorials=0, labs=0, credits=3.0,
        )
        db.add(course)
        db.flush()

        batch = Batch(program="BTech", branch="ICT", semester=4, section="A")
        db.add(batch)
        db.flush()

        db.add(BatchCourse(
            course_id=course.course_id,
            batch_id=batch.batch_id,
            students_enrolled=50,
        ))
        db.commit()

        validator = ValidationService(db)
        errors = validator.check_batch_slot_feasibility()

        assert len(errors) == 1
        assert "3" in errors[0]  # demand count
        assert "1" in errors[0]  # available slots
