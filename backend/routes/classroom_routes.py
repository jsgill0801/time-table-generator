"""
CRUD routes for Classroom entity.

Endpoints:
    GET    /               List all classrooms
    GET    /<name>         Get a single classroom
    POST   /               Create a new classroom
    PUT    /<name>         Update an existing classroom
    DELETE /<name>         Delete a classroom
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.classroom import Classroom
from backend.routes.auth_routes import login_required


classroom_bp = Blueprint("classrooms", __name__)


@classroom_bp.route("/", methods=["GET"])
@login_required
def list_classrooms():
    """Return all classrooms ordered by name."""
    db = next(get_db())
    try:
        rooms = db.query(Classroom).order_by(Classroom.classroom_name).all()
        return jsonify([r.to_dict() for r in rooms]), 200
    finally:
        db.close()


@classroom_bp.route("/<string:classroom_name>", methods=["GET"])
@login_required
def get_classroom(classroom_name):
    """Return a single classroom by its name."""
    db = next(get_db())
    try:
        room = db.query(Classroom).get(classroom_name.upper())
        if not room:
            return jsonify({"error": "Classroom not found."}), 404
        return jsonify(room.to_dict()), 200
    finally:
        db.close()


@classroom_bp.route("/", methods=["POST"])
@login_required
def create_classroom():
    """Create a new classroom."""
    data = request.get_json()
    db = next(get_db())
    try:
        name = data["classroom_name"].strip().upper()

        existing = db.query(Classroom).get(name)
        if existing:
            return jsonify({"error": "A classroom with this name already exists."}), 409

        room = Classroom(
            classroom_name=name,
            capacity=int(data["capacity"]),
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        return jsonify(room.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@classroom_bp.route("/<string:classroom_name>", methods=["PUT"])
@login_required
def update_classroom(classroom_name):
    """Update an existing classroom's capacity."""
    data = request.get_json()
    db = next(get_db())
    try:
        room = db.query(Classroom).get(classroom_name.upper())
        if not room:
            return jsonify({"error": "Classroom not found."}), 404

        if "capacity" in data:
            room.capacity = int(data["capacity"])

        db.commit()
        db.refresh(room)
        return jsonify(room.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@classroom_bp.route("/<string:classroom_name>", methods=["DELETE"])
@login_required
def delete_classroom(classroom_name):
    """Delete a classroom by its name."""
    db = next(get_db())
    try:
        room = db.query(Classroom).get(classroom_name.upper())
        if not room:
            return jsonify({"error": "Classroom not found."}), 404

        db.delete(room)
        db.commit()
        return jsonify({"message": "Classroom deleted."}), 200
    finally:
        db.close()
