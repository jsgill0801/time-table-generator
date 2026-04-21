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
from backend.routes.auth_routes import login_required


category_bp = Blueprint("categories", __name__)


@category_bp.route("/", methods=["GET"])
@login_required
def list_categories():
    """Return all categories ordered by name."""
    db = next(get_db())
    try:
        categories = db.query(Category).order_by(Category.category_name).all()
        return jsonify([c.to_dict() for c in categories]), 200
    finally:
        db.close()


@category_bp.route("/", methods=["POST"])
@login_required
def create_category():
    """Create a new category."""
    data = request.get_json()
    db = next(get_db())
    try:
        name = data["category_name"].strip()

        existing = db.query(Category).filter(
            Category.category_name == name
        ).first()
        if existing:
            return jsonify({"error": "This category already exists."}), 409

        category = Category(category_name=name)
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
@login_required
def update_category(category_id):
    """Rename a category."""
    data = request.get_json()
    db = next(get_db())
    try:
        category = db.query(Category).get(category_id)
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
@login_required
def delete_category(category_id):
    """Delete a category by its ID."""
    db = next(get_db())
    try:
        category = db.query(Category).get(category_id)
        if not category:
            return jsonify({"error": "Category not found."}), 404

        db.delete(category)
        db.commit()
        return jsonify({"message": "Category deleted."}), 200
    finally:
        db.close()
