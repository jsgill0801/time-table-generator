"""
CRUD routes for Category entity.

Endpoints:
    GET    /               List all categories
    POST   /               Create a new category
    PUT    /<id>           Update a category
    DELETE /<id>           Delete a category
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.category import Category
from backend.routes.auth_routes import login_required, admin_required, get_current_user_id


category_bp = Blueprint("categories", __name__)


@category_bp.route("/", methods=["GET"])
@login_required
def list_categories():
    """Return all categories ordered by name for the current user."""
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        categories = db.query(Category).filter(Category.user_id == user_id).order_by(Category.category_name).all()
        return jsonify([c.to_dict() for c in categories]), 200
    finally:
        db.close()


@category_bp.route("/", methods=["POST"])
@admin_required
def create_category():
    """Create a new category for the current user."""
    user_id = get_current_user_id()
    data = request.get_json()
    db = next(get_db())
    try:
        name = data["category_name"].strip()

        existing = db.query(Category).filter(
            Category.category_name == name,
            Category.user_id == user_id
        ).first()
        if existing:
            return jsonify({"error": "This category already exists."}), 409

        category = Category(
            user_id=user_id,
            category_name=name
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return jsonify(category.to_dict()), 201

    except (KeyError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@category_bp.route("/<int:category_id>", methods=["PUT"])
@admin_required
def update_category(category_id):
    """Rename a category if it belongs to the current user."""
    user_id = get_current_user_id()
    data = request.get_json()
    db = next(get_db())
    try:
        category = db.query(Category).filter(
            Category.category_id == category_id,
            Category.user_id == user_id
        ).first()
        if not category:
            return jsonify({"error": "Category not found."}), 404

        if "category_name" in data:
            category.category_name = data["category_name"].strip()

        db.commit()
        db.refresh(category)
        return jsonify(category.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@category_bp.route("/<int:category_id>", methods=["DELETE"])
@admin_required
def delete_category(category_id):
    """Delete a category by its ID if it belongs to the current user."""
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        category = db.query(Category).filter(
            Category.category_id == category_id,
            Category.user_id == user_id
        ).first()
        if not category:
            return jsonify({"error": "Category not found."}), 404

        # Delete dependent timetable and batch course mapping records
        from backend.models.batch_course import BatchCourse
        from backend.models.timetable import Timetable

        db.query(Timetable).filter(
            Timetable.batch_course_id.in_(
                db.query(BatchCourse.auto_id).filter(BatchCourse.category_id == category_id)
            )
        ).delete(synchronize_session=False)

        db.query(BatchCourse).filter(BatchCourse.category_id == category_id).delete(synchronize_session=False)

        db.delete(category)
        db.commit()
        return jsonify({"message": "Category deleted."}), 200
    finally:
        db.close()
