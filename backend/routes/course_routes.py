"""
CRUD routes for Course entity.

Endpoints:
    GET    /               List all courses
    GET    /<id>           Get a single course
    POST   /               Create a new course
    PUT    /<id>           Update an existing course
    DELETE /<id>           Delete a course
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.course import Course
from backend.routes.auth_routes import login_required


course_bp = Blueprint("courses", __name__)


@course_bp.route("/", methods=["GET"])
@login_required
def list_courses():
    """Return all courses ordered by course code."""
    db = next(get_db())
    try:
        courses = db.query(Course).order_by(Course.course_code).all()
        return jsonify([c.to_dict() for c in courses]), 200
    finally:
        db.close()


@course_bp.route("/<int:course_id>", methods=["GET"])
@login_required
def get_course(course_id):
    """Return a single course by its ID."""
    db = next(get_db())
    try:
        course = db.query(Course).get(course_id)
        if not course:
            return jsonify({"error": "Course not found."}), 404
        return jsonify(course.to_dict()), 200
    finally:
        db.close()


@course_bp.route("/", methods=["POST"])
@login_required
def create_course():
    """Create a new course."""
    data = request.get_json()
    db = next(get_db())
    try:
        # Check for duplicate course code
        existing = db.query(Course).filter(
            Course.course_code == data.get("course_code", "").strip().upper()
        ).first()
        if existing:
            return jsonify({"error": "A course with this code already exists."}), 409

        course = Course(
            course_code=data["course_code"].strip().upper(),
            course_name=data["course_name"].strip(),
            lectures=int(data["lectures"]),
            tutorials=int(data["tutorials"]),
            labs=int(data["labs"]),
            credits=float(data["credits"]),
        )
        db.add(course)
        db.commit()
        db.refresh(course)
        return jsonify(course.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@course_bp.route("/<int:course_id>", methods=["PUT"])
@login_required
def update_course(course_id):
    """Update an existing course."""
    data = request.get_json()
    db = next(get_db())
    try:
        course = db.query(Course).get(course_id)
        if not course:
            return jsonify({"error": "Course not found."}), 404

        # Update only the fields that were provided
        if "course_code" in data:
            course.course_code = data["course_code"].strip().upper()
        if "course_name" in data:
            course.course_name = data["course_name"].strip()
        if "lectures" in data:
            course.lectures = int(data["lectures"])
        if "tutorials" in data:
            course.tutorials = int(data["tutorials"])
        if "labs" in data:
            course.labs = int(data["labs"])
        if "credits" in data:
            course.credits = float(data["credits"])

        db.commit()
        db.refresh(course)
        return jsonify(course.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@course_bp.route("/<int:course_id>", methods=["DELETE"])
@login_required
def delete_course(course_id):
    """Delete a course by its ID."""
    db = next(get_db())
    try:
        course = db.query(Course).get(course_id)
        if not course:
            return jsonify({"error": "Course not found."}), 404

        db.delete(course)
        db.commit()
        return jsonify({"message": "Course deleted."}), 200
    finally:
        db.close()
