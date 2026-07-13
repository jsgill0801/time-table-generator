"""
CRUD routes for Batch entity.

Endpoints:
    GET    /               List all batches
    GET    /<id>           Get a single batch
    POST   /               Create a new batch
    PUT    /<id>           Update an existing batch
    DELETE /<id>           Delete a batch
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.batch import Batch
from backend.routes.auth_routes import login_required, admin_required, get_current_user_id


batch_bp = Blueprint("batches", __name__)


@batch_bp.route("/", methods=["GET"])
@login_required
def list_batches():
    """Return all batches for the current user, ordered by program and semester."""
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        batches = (
            db.query(Batch)
            .filter(Batch.user_id == user_id)
            .order_by(Batch.program, Batch.semester, Batch.branch)
            .all()
        )
        return jsonify([b.to_dict() for b in batches]), 200
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["GET"])
@login_required
def get_batch(batch_id):
    """Return a single batch by its ID if it belongs to the current user."""
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        batch = db.query(Batch).filter(
            Batch.batch_id == batch_id,
            Batch.user_id == user_id
        ).first()
        if not batch:
            return jsonify({"error": "Batch not found."}), 404
        return jsonify(batch.to_dict()), 200
    finally:
        db.close()


@batch_bp.route("/", methods=["POST"])
@admin_required
def create_batch():
    """Create a new batch for the current user."""
    user_id = get_current_user_id()
    data = request.get_json()
    db = next(get_db())
    try:
        batch = Batch(
            user_id=user_id,
            program=data["program"].strip(),
            branch=data["branch"].strip(),
            semester=int(data["semester"]),
            section=data.get("section", "").strip() or None,
        )
        db.add(batch)
        db.commit()
        db.refresh(batch)
        return jsonify(batch.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["PUT"])
@admin_required
def update_batch(batch_id):
    """Update an existing batch if it belongs to the current user."""
    user_id = get_current_user_id()
    data = request.get_json()
    db = next(get_db())
    try:
        batch = db.query(Batch).filter(
            Batch.batch_id == batch_id,
            Batch.user_id == user_id
        ).first()
        if not batch:
            return jsonify({"error": "Batch not found."}), 404

        if "program" in data:
            batch.program = data["program"].strip()
        if "branch" in data:
            batch.branch = data["branch"].strip()
        if "semester" in data:
            batch.semester = int(data["semester"])
        if "section" in data:
            batch.section = data["section"].strip() or None

        db.commit()
        db.refresh(batch)
        return jsonify(batch.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@batch_bp.route("/<int:batch_id>", methods=["DELETE"])
@admin_required
def delete_batch(batch_id):
    """Delete a batch by its ID if it belongs to the current user."""
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        batch = db.query(Batch).filter(
            Batch.batch_id == batch_id,
            Batch.user_id == user_id
        ).first()
        if not batch:
            return jsonify({"error": "Batch not found."}), 404

        db.delete(batch)
        db.commit()
        return jsonify({"message": "Batch deleted."}), 200
    finally:
        db.close()
