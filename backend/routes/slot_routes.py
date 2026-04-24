"""
CRUD routes for Slot entity.

Endpoints:
    GET    /               List all slots
    GET    /<slot_id>      Get a single slot
    POST   /               Create a new slot
    PUT    /<slot_id>      Update an existing slot
    DELETE /<slot_id>      Delete a slot
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.slot import Slot
from backend.routes.auth_routes import login_required
from backend.utils.helpers import DAY_ORDER


slot_bp = Blueprint("slots", __name__)


@slot_bp.route("/", methods=["GET"])
@login_required
def list_slots():
    """Return all slots sorted by day and start time."""
    db = next(get_db())
    try:
        slots = db.query(Slot).all()

        # Sort in Python using our day ordering (Mon -> Fri)
        slot_list = [s.to_dict() for s in slots]
        slot_list.sort(key=lambda s: (
            DAY_ORDER.get(s["day_of_week"], 99),
            s["start_time"],
        ))

        return jsonify(slot_list), 200
    finally:
        db.close()


@slot_bp.route("/<string:slot_id>", methods=["GET"])
@login_required
def get_slot(slot_id):
    """Return a single slot by its ID."""
    db = next(get_db())
    try:
        slot = db.query(Slot).get(slot_id)
        if not slot:
            return jsonify({"error": "Slot not found."}), 404
        return jsonify(slot.to_dict()), 200
    finally:
        db.close()


@slot_bp.route("/", methods=["POST"])
@login_required
def create_slot():
    """Create a new time slot."""
    data = request.get_json()
    db = next(get_db())
    try:
        sid = data["slot_id"].strip()

        existing = db.query(Slot).get(sid)
        if existing:
            return jsonify({"error": "A slot with this ID already exists."}), 409

        from datetime import time
        start_parts = data["start_time"].strip().split(":")
        end_parts = data["end_time"].strip().split(":")

        slot = Slot(
            slot_id=sid,
            day_of_week=data["day_of_week"].strip().title(),
            start_time=time(int(start_parts[0]), int(start_parts[1])),
            end_time=time(int(end_parts[0]), int(end_parts[1])),
            slot_name=data.get("slot_name", "").strip() or None,
        )
        db.add(slot)
        db.commit()
        db.refresh(slot)
        return jsonify(slot.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@slot_bp.route("/<string:slot_id>", methods=["PUT"])
@login_required
def update_slot(slot_id):
    """Update an existing slot."""
    data = request.get_json()
    db = next(get_db())
    try:
        slot = db.query(Slot).get(slot_id)
        if not slot:
            return jsonify({"error": "Slot not found."}), 404

        from datetime import time

        if "day_of_week" in data:
            slot.day_of_week = data["day_of_week"].strip().title()
        if "start_time" in data:
            parts = data["start_time"].strip().split(":")
            slot.start_time = time(int(parts[0]), int(parts[1]))
        if "end_time" in data:
            parts = data["end_time"].strip().split(":")
            slot.end_time = time(int(parts[0]), int(parts[1]))
        if "slot_name" in data:
            slot.slot_name = data["slot_name"].strip() or None

        db.commit()
        db.refresh(slot)
        return jsonify(slot.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@slot_bp.route("/<string:slot_id>", methods=["DELETE"])
@login_required
def delete_slot(slot_id):
    """Delete a slot by its ID."""
    db = next(get_db())
    try:
        slot = db.query(Slot).get(slot_id)
        if not slot:
            return jsonify({"error": "Slot not found."}), 404

        db.delete(slot)
        db.commit()
        return jsonify({"message": "Slot deleted."}), 200
    finally:
        db.close()
