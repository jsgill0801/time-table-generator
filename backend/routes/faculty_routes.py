"""
CRUD routes for Faculty entity.

Endpoints:
    GET    /               List all faculty members
    GET    /<code>         Get a single faculty member
    POST   /               Create a new faculty member
    PUT    /<code>         Update an existing faculty member
    DELETE /<code>         Delete a faculty member
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.faculty import Faculty
from backend.routes.auth_routes import login_required


faculty_bp = Blueprint("faculties", __name__)


@faculty_bp.route("/", methods=["GET"])
@login_required
def list_faculties():
    """Return all faculty ordered by code."""
    db = next(get_db())
    try:
        faculties = db.query(Faculty).order_by(Faculty.faculty_code).all()
        return jsonify([f.to_dict() for f in faculties]), 200
    finally:
        db.close()


@faculty_bp.route("/<string:faculty_code>", methods=["GET"])
@login_required
def get_faculty(faculty_code):
    """Return a single faculty member by their code."""
    db = next(get_db())
    try:
        faculty = db.query(Faculty).get(faculty_code.upper())
        if not faculty:
            return jsonify({"error": "Faculty not found."}), 404
        return jsonify(faculty.to_dict()), 200
    finally:
        db.close()


@faculty_bp.route("/", methods=["POST"])
@login_required
def create_faculty():
    """Create a new faculty member."""
    data = request.get_json()
    db = next(get_db())
    try:
        code = data["faculty_code"].strip().upper()

        existing = db.query(Faculty).get(code)
        if existing:
            return jsonify({"error": "A faculty with this code already exists."}), 409

        faculty = Faculty(
            faculty_code=code,
            faculty_name=data["faculty_name"].strip(),
            faculty_email=data.get("faculty_email", "").strip() or None,
            max_load=int(data["max_load"]),
        )
        db.add(faculty)
        db.commit()
        db.refresh(faculty)
        return jsonify(faculty.to_dict()), 201

    except (KeyError, ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@faculty_bp.route("/<string:faculty_code>", methods=["PUT"])
@login_required
def update_faculty(faculty_code):
    """Update an existing faculty member."""
    data = request.get_json()
    db = next(get_db())
    try:
        faculty = db.query(Faculty).get(faculty_code.upper())
        if not faculty:
            return jsonify({"error": "Faculty not found."}), 404

        if "faculty_name" in data:
            faculty.faculty_name = data["faculty_name"].strip()
        if "faculty_email" in data:
            faculty.faculty_email = data["faculty_email"].strip() or None
        if "max_load" in data:
            faculty.max_load = int(data["max_load"])

        db.commit()
        db.refresh(faculty)
        return jsonify(faculty.to_dict()), 200

    except (ValueError, TypeError) as e:
        db.rollback()
        return jsonify({"error": f"Invalid input: {e}"}), 400
    finally:
        db.close()


@faculty_bp.route("/<string:faculty_code>", methods=["DELETE"])
@login_required
def delete_faculty(faculty_code):
    """Delete a faculty member by their code."""
    db = next(get_db())
    try:
        faculty = db.query(Faculty).get(faculty_code.upper())
        if not faculty:
            return jsonify({"error": "Faculty not found."}), 404

        db.delete(faculty)
        db.commit()
        return jsonify({"message": "Faculty deleted."}), 200
    finally:
        db.close()
