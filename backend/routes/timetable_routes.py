"""
Timetable result routes.

Provides endpoints for retrieving the generated timetable
in various views: full grid, batch-wise, and faculty-wise.

Endpoints:
    GET /                   Full timetable (all assignments)
    GET /batch/<label>      Timetable filtered by batch
    GET /faculty/<code>     Timetable filtered by faculty
    GET /summary            Summary statistics of the generated timetable
"""

from collections import defaultdict

from flask import Blueprint, jsonify

from backend.db import get_db
from backend.models.timetable import Timetable
from backend.routes.auth_routes import login_required, get_current_user_id
from backend.utils.helpers import DAY_ORDER


timetable_bp = Blueprint("timetable", __name__)


# -----------------------------------------------------------------
#  GET / – full timetable
# -----------------------------------------------------------------

@timetable_bp.route("/", methods=["GET"])
@login_required
def get_full_timetable():
    """
    Return the full generated timetable, sorted by day and time for the current user.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        rows = db.query(Timetable).filter(Timetable.user_id == user_id).all()

        if not rows:
            return jsonify({
                "message": "No timetable found. Run generation first.",
                "timetable": [],
            }), 200

        # Convert and sort by day then time
        entries = [r.to_dict() for r in rows]
        entries.sort(key=lambda e: (
            DAY_ORDER.get(e["day_of_week"], 99),
            e["start_time"],
        ))
        generated_at = max(
            (entry.get("generated_at") for entry in entries if entry.get("generated_at")),
            default=None,
        )

        return jsonify({
            "message": f"{len(entries)} scheduled session(s).",
            "generated_at": generated_at,
            "timetable": entries,
        }), 200

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /batch/<label> – batch-wise timetable
# -----------------------------------------------------------------

@timetable_bp.route("/batch/<string:batch_label>", methods=["GET"])
@login_required
def get_batch_timetable(batch_label):
    """
    Return timetable entries for a specific batch for the current user.

    The batch_label should be URL-encoded if it contains spaces.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        rows = (
            db.query(Timetable)
            .filter(
                Timetable.batch_label == batch_label,
                Timetable.user_id == user_id
            )
            .all()
        )

        if not rows:
            return jsonify({
                "message": f"No timetable entries found for batch '{batch_label}'.",
                "timetable": [],
            }), 200

        entries = [r.to_dict() for r in rows]
        entries.sort(key=lambda e: (
            DAY_ORDER.get(e["day_of_week"], 99),
            e["start_time"],
        ))

        return jsonify({
            "batch_label": batch_label,
            "message": f"{len(entries)} session(s) for '{batch_label}'.",
            "timetable": entries,
        }), 200

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /faculty/<code> – faculty-wise timetable
# -----------------------------------------------------------------

@timetable_bp.route("/faculty/<string:faculty_code>", methods=["GET"])
@login_required
def get_faculty_timetable(faculty_code):
    """
    Return timetable entries for a specific faculty member for the current user.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        rows = (
            db.query(Timetable)
            .filter(
                Timetable.faculty_code == faculty_code.upper(),
                Timetable.user_id == user_id
            )
            .all()
        )

        if not rows:
            return jsonify({
                "message": f"No timetable entries found for faculty '{faculty_code}'.",
                "timetable": [],
            }), 200

        entries = [r.to_dict() for r in rows]
        entries.sort(key=lambda e: (
            DAY_ORDER.get(e["day_of_week"], 99),
            e["start_time"],
        ))

        return jsonify({
            "faculty_code": faculty_code.upper(),
            "message": f"{len(entries)} session(s) for faculty '{faculty_code}'.",
            "timetable": entries,
        }), 200

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /summary – timetable summary statistics
# -----------------------------------------------------------------

@timetable_bp.route("/summary", methods=["GET"])
@login_required
def get_timetable_summary():
    """
    Return high-level statistics about the generated timetable for the current user.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        rows = db.query(Timetable).filter(Timetable.user_id == user_id).all()

        if not rows:
            return jsonify({
                "message": "No timetable found. Run generation first.",
                "summary": {},
            }), 200

        # Collect unique values
        batches = set()
        faculties = set()
        rooms = set()
        courses = set()
        days_used = set()

        # Faculty load: how many sessions each faculty teaches
        faculty_load = defaultdict(int)

        # Room utilisation: how many sessions per room
        room_usage = defaultdict(int)

        for r in rows:
            batches.add(r.batch_label)
            if r.faculty_code:
                faculties.add(r.faculty_code)
                faculty_load[r.faculty_code] += 1
            rooms.add(r.classroom_name)
            courses.add(r.course_code)
            days_used.add(r.day_of_week)
            room_usage[r.classroom_name] += 1

        summary = {
            "total_sessions": len(rows),
            "unique_courses": len(courses),
            "unique_batches": len(batches),
            "unique_faculties": len(faculties),
            "unique_rooms": len(rooms),
            "generated_at": max(
                (r.generated_at.isoformat() + "Z" for r in rows if r.generated_at),
                default=None,
            ),
            "days_used": sorted(days_used, key=lambda d: DAY_ORDER.get(d, 99)),
            "batches": sorted(batches),
            "faculty_load": dict(sorted(faculty_load.items())),
            "room_usage": dict(sorted(room_usage.items())),
        }

        return jsonify({
            "message": "Timetable summary.",
            "summary": summary,
        }), 200

    finally:
        db.close()
