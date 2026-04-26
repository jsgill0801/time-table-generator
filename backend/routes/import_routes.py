"""
CSV import routes.

Accepts CSV file uploads for each entity type, validates
every row using the appropriate parser, and bulk-inserts
the records into the database.

Endpoints:
    POST /courses          Import courses from CSV
    POST /batches          Import batches from CSV
    POST /faculties        Import faculty from CSV
    POST /classrooms       Import classrooms from CSV
    POST /slots            Import slots from CSV
    POST /batch-courses    Import batch-course mappings from CSV
    POST /faculty-courses  Import faculty-course mappings from CSV
"""

from flask import Blueprint, request, jsonify
from datetime import time as dt_time
import csv
import io

from backend.db import get_db
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
from backend.parsers.course_bundle_parser import CourseBundleParser

from backend.routes.auth_routes import login_required, admin_required
from backend.utils.errors import DataError


import_bp = Blueprint("import", __name__)


def _read_csv_from_request():
    """
    Extract CSV text from the request.

    Supports two formats:
        1. File upload via multipart/form-data (field name: "file")
        2. Raw CSV text in the JSON body (field name: "csv_content")

    Returns the CSV content as a string.
    """
    # Try file upload first
    if "file" in request.files:
        file = request.files["file"]
        return file.read().decode("utf-8-sig")

    # Fall back to JSON body
    data = request.get_json(silent=True)
    if data and "csv_content" in data:
        return data["csv_content"]

    return None


def _get_csv_headers(csv_text: str) -> set[str]:
    """Return the normalized CSV headers for the uploaded content."""
    reader = csv.DictReader(io.StringIO(csv_text))

    if reader.fieldnames is None:
        return set()

    return {name.strip() for name in reader.fieldnames if name}


def _import_course_bundle(db, csv_text: str):
    """Import courses plus their batch/faculty mappings from one CSV."""
    batches = db.query(Batch).order_by(Batch.program, Batch.semester, Batch.branch).all()
    faculty_rows = db.query(Faculty).order_by(Faculty.faculty_code).all()

    if not batches:
        raise DataError(
            "batches",
            "No batches found. Import batches before importing the combined courses CSV.",
        )

    if not faculty_rows:
        raise DataError(
            "faculty",
            "No faculty found. Import faculty before importing the combined courses CSV.",
        )

    batch_lookup = {batch.label: batch for batch in batches}
    faculty_lookup = {}

    for faculty in faculty_rows:
        faculty_lookup[faculty.faculty_code] = faculty.faculty_code
        faculty_lookup[faculty.faculty_name] = faculty.faculty_code

    parser = CourseBundleParser(set(batch_lookup.keys()), faculty_lookup)
    rows = parser.parse(csv_text)

    category_lookup = {
        category.category_name: category
        for category in db.query(Category).all()
    }

    course_created = 0
    course_skipped = 0
    batch_created = 0
    batch_skipped = 0
    faculty_created = 0
    faculty_skipped = 0

    for row in rows:
        course = db.query(Course).filter(
            Course.course_code == row["course_code"]
        ).first()

        if not course:
            course = Course(
                course_code=row["course_code"],
                course_name=row["course_name"],
                lectures=row["lectures"],
                tutorials=row["tutorials"],
                labs=row["labs"],
                credits=row["credits"],
            )
            db.add(course)
            db.flush()
            course_created += 1
        else:
            course_skipped += 1

        existing_faculty_link = db.query(FacultyCourse).filter(
            FacultyCourse.course_id == course.course_id,
            FacultyCourse.faculty_code == row["faculty_code"],
        ).first()

        if existing_faculty_link:
            faculty_skipped += 1
        else:
            db.add(FacultyCourse(
                course_id=course.course_id,
                faculty_code=row["faculty_code"],
            ))
            faculty_created += 1

        for mapping in row["batch_mappings"]:
            batch = batch_lookup[mapping["batch_label"]]
            category = None

            if mapping["category"]:
                category = category_lookup.get(mapping["category"])

                if not category:
                    category = Category(category_name=mapping["category"])
                    db.add(category)
                    db.flush()
                    category_lookup[category.category_name] = category

            existing_batch_link = db.query(BatchCourse).filter(
                BatchCourse.course_id == course.course_id,
                BatchCourse.batch_id == batch.batch_id,
            ).first()

            if existing_batch_link:
                batch_skipped += 1
                continue

            db.add(BatchCourse(
                course_id=course.course_id,
                batch_id=batch.batch_id,
                category_id=category.category_id if category else None,
                students_enrolled=mapping["students_enrolled"],
            ))
            batch_created += 1

    db.commit()

    return jsonify({
        "message": (
            "Import complete. "
            f"{course_created} courses created, {course_skipped} existing, "
            f"{batch_created} batch mappings created, {batch_skipped} existing, "
            f"{faculty_created} faculty links created, {faculty_skipped} existing."
        ),
        "created_courses": course_created,
        "skipped_courses": course_skipped,
        "created_batch_mappings": batch_created,
        "skipped_batch_mappings": batch_skipped,
        "created_faculty_links": faculty_created,
        "skipped_faculty_links": faculty_skipped,
    }), 201


# -----------------------------------------------------------------
#  POST /courses – import courses from CSV
# -----------------------------------------------------------------

@import_bp.route("/courses", methods=["POST"])
@admin_required
def import_courses():
    """Parse and insert courses from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        headers = _get_csv_headers(csv_text)

        if "batches" in headers or "faculty" in headers:
            return _import_course_bundle(db, csv_text)

        # Parse and validate
        parser = CourseParser()
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            # Skip if course code already exists
            existing = db.query(Course).filter(
                Course.course_code == row["course_code"]
            ).first()

            if existing:
                skipped += 1
                continue

            course = Course(
                course_code=row["course_code"],
                course_name=row["course_name"],
                lectures=row["lectures"],
                tutorials=row["tutorials"],
                labs=row["labs"],
                credits=row["credits"],
            )
            db.add(course)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /batches – import batches from CSV
# -----------------------------------------------------------------

@import_bp.route("/batches", methods=["POST"])
@admin_required
def import_batches():
    """Parse and insert batches from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        parser = BatchParser()
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            existing = db.query(Batch).filter(
                Batch.program == row["program"],
                Batch.branch == row["branch"],
                Batch.semester == row["semester"],
                Batch.section == row["section"],
            ).first()

            if existing:
                skipped += 1
                continue

            batch = Batch(
                program=row["program"],
                branch=row["branch"],
                semester=row["semester"],
                section=row["section"],
            )
            db.add(batch)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /faculties – import faculty from CSV
# -----------------------------------------------------------------

@import_bp.route("/faculties", methods=["POST"])
@admin_required
def import_faculties():
    """Parse and insert faculty members from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        parser = FacultyParser()
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            existing = db.query(Faculty).get(row["faculty_code"])

            if existing:
                skipped += 1
                continue

            faculty = Faculty(
                faculty_code=row["faculty_code"],
                faculty_name=row["faculty_name"],
                faculty_email=row["faculty_email"],
                max_load=row["max_load"],
            )
            db.add(faculty)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /classrooms – import classrooms from CSV
# -----------------------------------------------------------------

@import_bp.route("/classrooms", methods=["POST"])
@admin_required
def import_classrooms():
    """Parse and insert classrooms from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        parser = ClassroomParser()
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            existing = db.query(Classroom).get(row["classroom_name"])

            if existing:
                skipped += 1
                continue

            room = Classroom(
                classroom_name=row["classroom_name"],
                capacity=row["capacity"],
            )
            db.add(room)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /slots – import slots from CSV
# -----------------------------------------------------------------

@import_bp.route("/slots", methods=["POST"])
@admin_required
def import_slots():
    """Parse and insert time slots from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        parser = SlotParser()
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            existing = db.query(Slot).get(row["slot_id"])

            if existing:
                skipped += 1
                continue

            # Convert "HH:MM" strings to time objects
            start_parts = row["start_time"].split(":")
            end_parts = row["end_time"].split(":")

            slot = Slot(
                slot_id=row["slot_id"],
                day_of_week=row["day_of_week"],
                start_time=dt_time(int(start_parts[0]), int(start_parts[1])),
                end_time=dt_time(int(end_parts[0]), int(end_parts[1])),
                slot_name=row["slot_name"],
            )
            db.add(slot)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /categories – import categories from CSV
# -----------------------------------------------------------------

@import_bp.route("/categories", methods=["POST"])
@admin_required
def import_categories():
    """Parse and insert categories from a CSV file."""
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        reader = csv.DictReader(io.StringIO(csv_text))

        created = 0
        skipped = 0

        for row in reader:
            name = row.get("category_name", "").strip()
            if not name:
                continue

            existing = db.query(Category).filter(
                Category.category_name == name
            ).first()

            if existing:
                skipped += 1
                continue

            cat = Category(category_name=name)
            db.add(cat)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /batch-courses – import batch-course mappings from CSV
# -----------------------------------------------------------------

@import_bp.route("/batch-courses", methods=["POST"])
@admin_required
def import_batch_courses():
    """
    Parse and insert batch-course mappings from a CSV file.

    This endpoint requires that courses and batches have
    already been imported, since the parser performs FK validation.
    """
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        # Build the known-entity sets for FK validation
        known_course_codes = {
            c.course_code for c in db.query(Course).all()
        }

        known_batches = [
            {
                "program": b.program,
                "branch": b.branch,
                "semester": b.semester,
                "section": b.section,
            }
            for b in db.query(Batch).all()
        ]

        # Parse with FK validation
        parser = BatchCourseParser(known_course_codes, known_batches)
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            # Resolve the course_id and batch_id from the codes/identifiers
            course = db.query(Course).filter(
                Course.course_code == row["course_code"]
            ).first()

            batch = db.query(Batch).filter(
                Batch.program == row["program"],
                Batch.branch == row["branch"],
                Batch.semester == row["semester"],
                Batch.section == row["section"],
            ).first()

            # Skip if this mapping already exists
            existing = db.query(BatchCourse).filter(
                BatchCourse.course_id == course.course_id,
                BatchCourse.batch_id == batch.batch_id,
            ).first()

            if existing:
                skipped += 1
                continue

            # Resolve or create the category if provided
            category_id = None
            if row["category"]:
                cat = db.query(Category).filter(
                    Category.category_name == row["category"]
                ).first()

                if not cat:
                    cat = Category(category_name=row["category"])
                    db.add(cat)
                    db.flush()  # get the ID without committing

                category_id = cat.category_id

            bc = BatchCourse(
                course_id=course.course_id,
                batch_id=batch.batch_id,
                category_id=category_id,
                students_enrolled=row["students_enrolled"],
            )
            db.add(bc)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /faculty-courses – import faculty-course mappings from CSV
# -----------------------------------------------------------------

@import_bp.route("/faculty-courses", methods=["POST"])
@admin_required
def import_faculty_courses():
    """
    Parse and insert faculty-course mappings from a CSV file.

    This endpoint requires that faculty and courses have
    already been imported, since the parser performs FK validation.
    """
    csv_text = _read_csv_from_request()
    if not csv_text:
        return jsonify({"error": "No CSV data provided."}), 400

    db = next(get_db())
    try:
        # Build the known-entity sets for FK validation
        known_faculty_codes = {
            f.faculty_code for f in db.query(Faculty).all()
        }

        known_course_codes = {
            c.course_code for c in db.query(Course).all()
        }

        # Parse with FK validation
        parser = FacultyCourseParser(known_faculty_codes, known_course_codes)
        rows = parser.parse(csv_text)

        created = 0
        skipped = 0

        for row in rows:
            course = db.query(Course).filter(
                Course.course_code == row["course_code"]
            ).first()

            # Skip if this mapping already exists
            existing = db.query(FacultyCourse).filter(
                FacultyCourse.course_id == course.course_id,
                FacultyCourse.faculty_code == row["faculty_code"],
            ).first()

            if existing:
                skipped += 1
                continue

            fc = FacultyCourse(
                course_id=course.course_id,
                faculty_code=row["faculty_code"],
            )
            db.add(fc)
            created += 1

        db.commit()

        return jsonify({
            "message": f"Import complete. {created} created, {skipped} skipped (duplicates).",
            "created": created,
            "skipped": skipped,
        }), 201

    except DataError as e:
        db.rollback()
        return jsonify({"error": str(e)}), 400
    finally:
        db.close()
