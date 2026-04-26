"""
CRUD routes for FacultyCourse mapping.

These endpoints manage the assignment of faculty to courses.

Endpoints:
    GET    /               List all faculty-course mappings (with joined info)
    POST   /               Assign a faculty member to a course
    DELETE /<id>           Remove a faculty-course assignment
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.faculty_course import FacultyCourse
from backend.models.course import Course
from backend.models.faculty import Faculty
from backend.routes.auth_routes import login_required, admin_required


faculty_course_bp = Blueprint("faculty_courses", __name__)


@faculty_course_bp.route("/", methods=["GET"])
@login_required
def list_faculty_courses():
    """Return all faculty-course mappings with joined details."""
    db = next(get_db())
    try:
        results = (
            db.query(FacultyCourse, Faculty, Course)
            .join(Faculty, FacultyCourse.faculty_code == Faculty.faculty_code)
            .join(Course, FacultyCourse.course_id == Course.course_id)
            .order_by(Faculty.faculty_code, Course.course_code)
            .all()
        )

        output = []
        for fc, faculty, course in results:
            output.append({
                "auto_id": fc.auto_id,
                "faculty_code": faculty.faculty_code,
                "faculty_name": faculty.faculty_name,
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
            })

        return jsonify(output), 200
    finally:
        db.close()


@faculty_course_bp.route("/", methods=["POST"])
@admin_required
def create_faculty_course():
    """Assign a faculty member to a course."""
    data = request.get_json()
    db = next(get_db())
    try:
        course_id = int(data["course_id"])
        faculty_code = data["faculty_code"].strip().upper()

        # Verify the course and faculty exist
        if not db.query(Course).get(course_id):
            return jsonify({"error": "Course not found."}), 404
        if not db.query(Faculty).get(faculty_code):
            return jsonify({"error": "Faculty not found."}), 404

        # Check for duplicate
        existing = db.query(FacultyCourse).filter(
            FacultyCourse.course_id == course_id,
            FacultyCourse.faculty_code == faculty_code,
        ).first()
        if existing:
            return jsonify({"error": "This faculty is already assigned to this course."}), 409

        fc = FacultyCourse(
            course_id=course_id,
            faculty_code=faculty_code,
        )
        db.add(fc)
        db.commit()
        db.refresh(fc)
        return jsonify(fc.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@faculty_course_bp.route("/<int:auto_id>", methods=["DELETE"])
@admin_required
def delete_faculty_course(auto_id):
    """Remove a faculty-course assignment."""
    db = next(get_db())
    try:
        fc = db.query(FacultyCourse).get(auto_id)
        if not fc:
            return jsonify({"error": "Faculty-course mapping not found."}), 404

        db.delete(fc)
        db.commit()
        return jsonify({"message": "Faculty-course mapping deleted."}), 200
    finally:
        db.close()
