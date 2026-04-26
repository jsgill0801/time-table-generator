"""
Database seeder – loads sample CSV data into the database.

Reads all CSV files from the sample_data/ directory and inserts
records using the parser layer for validation. Must be run in
a specific order because of foreign-key dependencies:

    1. Courses (no dependencies)
    2. Batches (no dependencies)
    3. Faculty (no dependencies)
    4. Classrooms (no dependencies)
    5. Slots (no dependencies)
    6. Batch-Courses (depends on courses, batches)
    7. Faculty-Courses (depends on faculty, courses)

Usage:
    python -m backend.seed
"""

import os
import sys
from datetime import time as dt_time

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import get_db, init_db
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse

from backend.parsers.course_parser import CourseParser
from backend.parsers.batch_parser import BatchParser
from backend.parsers.faculty_parser import FacultyParser
from backend.parsers.classroom_parser import ClassroomParser
from backend.parsers.slot_parser import SlotParser
from backend.parsers.batch_course_parser import BatchCourseParser
from backend.parsers.faculty_course_parser import FacultyCourseParser

from backend.utils.errors import DataError


# Path to the sample data directory
SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "sample_data",
)


def _read_csv(filename: str) -> str:
    """Read a CSV file from the sample_data directory."""
    path = os.path.join(SAMPLE_DIR, filename)
    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def seed_courses(db) -> int:
    """Parse and insert sample courses."""
    parser = CourseParser()
    rows = parser.parse(_read_csv("courses.csv"))

    count = 0
    for row in rows:
        existing = db.query(Course).filter(
            Course.course_code == row["course_code"]
        ).first()
        if existing:
            continue

        db.add(Course(
            course_code=row["course_code"],
            course_name=row["course_name"],
            lectures=row["lectures"],
            tutorials=row["tutorials"],
            labs=row["labs"],
            credits=row["credits"],
        ))
        count += 1

    db.commit()
    return count


def seed_batches(db) -> int:
    """Parse and insert sample batches."""
    parser = BatchParser()
    rows = parser.parse(_read_csv("batches.csv"))

    count = 0
    for row in rows:
        existing = db.query(Batch).filter(
            Batch.program == row["program"],
            Batch.branch == row["branch"],
            Batch.semester == row["semester"],
            Batch.section == row["section"],
        ).first()
        if existing:
            continue

        db.add(Batch(
            program=row["program"],
            branch=row["branch"],
            semester=row["semester"],
            section=row["section"],
        ))
        count += 1

    db.commit()
    return count


def seed_faculty(db) -> int:
    """Parse and insert sample faculty members."""
    parser = FacultyParser()
    rows = parser.parse(_read_csv("faculties.csv"))

    count = 0
    for row in rows:
        existing = db.query(Faculty).get(row["faculty_code"])
        if existing:
            continue

        db.add(Faculty(
            faculty_code=row["faculty_code"],
            faculty_name=row["faculty_name"],
            faculty_email=row["faculty_email"],
            max_load=row["max_load"],
        ))
        count += 1

    db.commit()
    return count


def seed_classrooms(db) -> int:
    """Parse and insert sample classrooms."""
    parser = ClassroomParser()
    rows = parser.parse(_read_csv("classrooms.csv"))

    count = 0
    for row in rows:
        existing = db.query(Classroom).get(row["classroom_name"])
        if existing:
            continue

        db.add(Classroom(
            classroom_name=row["classroom_name"],
            capacity=row["capacity"],
        ))
        count += 1

    db.commit()
    return count


def seed_slots(db) -> int:
    """Parse and insert sample time slots."""
    parser = SlotParser()
    rows = parser.parse(_read_csv("slots.csv"))

    count = 0
    for row in rows:
        existing = db.query(Slot).get(row["slot_id"])
        if existing:
            continue

        start_parts = row["start_time"].split(":")
        end_parts = row["end_time"].split(":")

        db.add(Slot(
            slot_id=row["slot_id"],
            day_of_week=row["day_of_week"],
            start_time=dt_time(int(start_parts[0]), int(start_parts[1])),
            end_time=dt_time(int(end_parts[0]), int(end_parts[1])),
            slot_name=row["slot_name"],
        ))
        count += 1

    db.commit()
    return count


def seed_batch_courses(db) -> int:
    """Parse and insert sample batch-course mappings."""
    # Build known-entity sets for FK validation
    known_course_codes = {c.course_code for c in db.query(Course).all()}
    known_batches = [
        {
            "program": b.program,
            "branch": b.branch,
            "semester": b.semester,
            "section": b.section,
        }
        for b in db.query(Batch).all()
    ]

    parser = BatchCourseParser(known_course_codes, known_batches)
    rows = parser.parse(_read_csv("batch_courses.csv"))

    count = 0
    for row in rows:
        course = db.query(Course).filter(
            Course.course_code == row["course_code"]
        ).first()

        batch = db.query(Batch).filter(
            Batch.program == row["program"],
            Batch.branch == row["branch"],
            Batch.semester == row["semester"],
            Batch.section == row["section"],
        ).first()

        # Check for duplicates
        existing = db.query(BatchCourse).filter(
            BatchCourse.course_id == course.course_id,
            BatchCourse.batch_id == batch.batch_id,
        ).first()
        if existing:
            continue

        # Resolve or create category
        category_id = None
        if row["category"]:
            cat = db.query(Category).filter(
                Category.category_name == row["category"]
            ).first()
            if not cat:
                cat = Category(category_name=row["category"])
                db.add(cat)
                db.flush()
            category_id = cat.category_id

        db.add(BatchCourse(
            course_id=course.course_id,
            batch_id=batch.batch_id,
            category_id=category_id,
            students_enrolled=row["students_enrolled"],
        ))
        count += 1

    db.commit()
    return count


def seed_faculty_courses(db) -> int:
    """Parse and insert sample faculty-course mappings."""
    known_faculty_codes = {f.faculty_code for f in db.query(Faculty).all()}
    known_course_codes = {c.course_code for c in db.query(Course).all()}

    parser = FacultyCourseParser(known_faculty_codes, known_course_codes)
    rows = parser.parse(_read_csv("faculty_courses.csv"))

    count = 0
    for row in rows:
        course = db.query(Course).filter(
            Course.course_code == row["course_code"]
        ).first()

        existing = db.query(FacultyCourse).filter(
            FacultyCourse.course_id == course.course_id,
            FacultyCourse.faculty_code == row["faculty_code"],
        ).first()
        if existing:
            continue

        db.add(FacultyCourse(
            course_id=course.course_id,
            faculty_code=row["faculty_code"],
        ))
        count += 1

    db.commit()
    return count


SEED_STEPS = [
    ("courses", seed_courses),
    ("batches", seed_batches),
    ("faculty", seed_faculty),
    ("classrooms", seed_classrooms),
    ("slots", seed_slots),
    ("batch_courses", seed_batch_courses),
    ("faculty_courses", seed_faculty_courses),
]


def seed_dataset(db) -> tuple[dict[str, int], int]:
    """Seed the sample dataset and return per-step counts plus the total."""
    summary = {}
    total = 0

    for key, func in SEED_STEPS:
        count = func(db)
        summary[key] = count
        total += count

    return summary, total


def run_seed():
    """
    Execute the full seeding process in dependency order.
    Prints a summary of inserted records.
    """
    print("Initialising database tables...")
    init_db()

    db = next(get_db())

    try:
        print("\nSeeding sample data:")
        print("-" * 40)
        summary, total = seed_dataset(db)

        labels = {
            "courses": "Courses",
            "batches": "Batches",
            "faculty": "Faculty",
            "classrooms": "Classrooms",
            "slots": "Slots",
            "batch_courses": "Batch-Courses",
            "faculty_courses": "Faculty-Courses",
        }

        for key, count in summary.items():
            print(f"  {labels[key]:20s} -> {count} record(s) inserted")

        print("-" * 40)
        print(f"  Total: {total} record(s) inserted")
        print("\nSeeding complete.")

    except DataError as e:
        print(f"\nSeeding failed: {e}")
        db.rollback()
        sys.exit(1)

    except Exception as e:
        print(f"\nUnexpected error: {e}")
        db.rollback()
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
