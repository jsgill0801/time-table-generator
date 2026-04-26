"""
CRUD routes for BatchCourse mapping.

These endpoints manage the assignment of courses to batches,
including the category and enrollment count.

Endpoints:
    GET    /               List all batch-course mappings (with joined info)
    POST   /               Create a new mapping
    PUT    /<id>           Update enrollment or category
    DELETE /<id>           Remove a mapping
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.batch_course import BatchCourse
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.category import Category
from backend.routes.auth_routes import login_required, admin_required
from backend.utils.helpers import format_ltpc


batch_course_bp = Blueprint("batch_courses", __name__)


@batch_course_bp.route("/", methods=["GET"])
@login_required
def list_batch_courses():
    """Return all batch-course mappings with joined details."""
    db = next(get_db())
    try:
        results = (
            db.query(BatchCourse, Course, Batch, Category)
            .join(Course, BatchCourse.course_id == Course.course_id)
            .join(Batch, BatchCourse.batch_id == Batch.batch_id)
            .outerjoin(Category, BatchCourse.category_id == Category.category_id)
            .order_by(Batch.program, Batch.semester, Course.course_code)
            .all()
        )

        output = []
        for bc, course, batch, category in results:
            output.append({
                "auto_id": bc.auto_id,
                "course_id": course.course_id,
                "course_code": course.course_code,
                "course_name": course.course_name,
                "ltpc": format_ltpc(
                    course.lectures, course.tutorials,
                    course.labs, course.credits,
                ),
                "batch_id": batch.batch_id,
                "batch_label": batch.label,
                "category_id": bc.category_id,
                "category_name": category.category_name if category else None,
                "students_enrolled": bc.students_enrolled,
            })

        return jsonify(output), 200
    finally:
        db.close()


@batch_course_bp.route("/", methods=["POST"])
@admin_required
def create_batch_course():
    """Assign a course to a batch."""
    data = request.get_json()
    db = next(get_db())
    try:
        course_id = int(data["course_id"])
        batch_id = int(data["batch_id"])

        # Verify the course and batch exist
        if not db.query(Course).get(course_id):
            return jsonify({"error": "Course not found."}), 404
        if not db.query(Batch).get(batch_id):
            return jsonify({"error": "Batch not found."}), 404

        # Check for duplicate mapping
        existing = db.query(BatchCourse).filter(
            BatchCourse.course_id == course_id,
            BatchCourse.batch_id == batch_id,
        ).first()
        if existing:
            return jsonify({"error": "This course is already assigned to this batch."}), 409

        bc = BatchCourse(
            course_id=course_id,
            batch_id=batch_id,
            category_id=int(data["category_id"]) if data.get("category_id") else None,
            students_enrolled=int(data["students_enrolled"]),
        )
        db.add(bc)
        db.commit()
        db.refresh(bc)
        return jsonify(bc.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@batch_course_bp.route("/<int:auto_id>", methods=["PUT"])
@admin_required
def update_batch_course(auto_id):
    """Update a batch-course mapping (enrollment count or category)."""
    data = request.get_json()
    db = next(get_db())
    try:
        bc = db.query(BatchCourse).get(auto_id)
        if not bc:
            return jsonify({"error": "Batch-course mapping not found."}), 404

        if "students_enrolled" in data:
            bc.students_enrolled = int(data["students_enrolled"])
        if "category_id" in data:
            bc.category_id = int(data["category_id"]) if data["category_id"] else None

        db.commit()
        db.refresh(bc)
        return jsonify(bc.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@batch_course_bp.route("/<int:auto_id>", methods=["DELETE"])
@admin_required
def delete_batch_course(auto_id):
    """Remove a course from a batch."""
    db = next(get_db())
    try:
        bc = db.query(BatchCourse).get(auto_id)
        if not bc:
            return jsonify({"error": "Batch-course mapping not found."}), 404

        db.delete(bc)
        db.commit()
        return jsonify({"message": "Batch-course mapping deleted."}), 200
    finally:
        db.close()
