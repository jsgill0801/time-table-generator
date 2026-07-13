"""
Export routes – Excel download endpoints.

All operations are scoped to the current user's data.

Endpoints:
    GET /download/overall     Download the overall timetable (single sheet)
    GET /download/faculty     Download faculty-wise timetable (one sheet per faculty)
    GET /download/batch       Download batch-wise timetable (one sheet per batch)
    GET /download/room        Download room-wise timetable (one sheet per room)
    GET /preview              Preview timetable grid as JSON
"""

import os
import logging
import json
from datetime import datetime

from flask import Blueprint, send_file, jsonify

from backend.db import get_db
from backend.models.timetable import Timetable
from backend.models.slot import Slot
from backend.services.export_service import ExportService
from backend.routes.auth_routes import login_required, get_current_user_id

logger = logging.getLogger(__name__)
DEBUG_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "debug-ecec21.log",
)

export_bp = Blueprint("export", __name__)


def _debug_log(hypothesis_id: str, location: str, message: str, data: dict):
    # region agent log
    try:
        payload = {
            "sessionId": "ecec21",
            "runId": f"export_route_{int(datetime.now().timestamp() * 1000)}",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=True) + "\n")
    except Exception:
        pass
    # endregion


def _build_export_service(db, user_id):
    """Fetch timetable data for the current user and create the ExportService instance."""
    rows = db.query(Timetable).filter(Timetable.user_id == user_id).all()

    if not rows:
        return None, None

    timetable_data = [r.to_dict() for r in rows]
    slot_data = [slot.to_dict() for slot in db.query(Slot).filter(Slot.user_id == user_id).all()]
    service = ExportService(timetable_data, slot_data)
    return service, timetable_data


def _download(generate_method, label):
    """Shared logic for all four download endpoints."""
    _debug_log("H6", "export_routes.py:_download", "Entered download route", {"label": label})
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        service, _ = _build_export_service(db, user_id)

        if service is None:
            return jsonify({
                "error": "No timetable data found",
                "message": "Run timetable generation first before downloading.",
            }), 404

        filepath = generate_method(service)
        logger.info("Excel file generated (%s): %s", label, filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        logger.error("Excel export failed (%s): %s", label, str(e))
        return jsonify({
            "error": "Export failed",
            "message": f"Failed to generate Excel file: {str(e)}",
        }), 500

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /download/overall
# -----------------------------------------------------------------

@export_bp.route("/download/overall", methods=["GET"])
@login_required
def download_overall():
    """Overall timetable — single sheet, all batches."""
    return _download(lambda svc: svc.generate_overall(), "overall")


# -----------------------------------------------------------------
#  GET /download/faculty
# -----------------------------------------------------------------

@export_bp.route("/download/faculty", methods=["GET"])
@login_required
def download_faculty():
    """Faculty-wise timetable — one sheet per faculty."""
    return _download(lambda svc: svc.generate_faculty_wise(), "faculty")


# -----------------------------------------------------------------
#  GET /download/batch
# -----------------------------------------------------------------

@export_bp.route("/download/batch", methods=["GET"])
@login_required
def download_batch():
    """Batch-wise timetable — one sheet per batch."""
    return _download(lambda svc: svc.generate_batch_wise(), "batch")


# -----------------------------------------------------------------
#  GET /download/room
# -----------------------------------------------------------------

@export_bp.route("/download/room", methods=["GET"])
@login_required
def download_room():
    """Room-wise timetable — one sheet per room."""
    return _download(lambda svc: svc.generate_room_wise(), "room")


@export_bp.route("/download/batches", methods=["GET"])
@login_required
def download_batches_alias():
    """Alias: batch-wise timetable (plural path)."""
    return _download(lambda svc: svc.generate_batch_wise(), "batch-alias")


@export_bp.route("/download/rooms", methods=["GET"])
@login_required
def download_rooms_alias():
    """Alias: room-wise timetable (plural path)."""
    return _download(lambda svc: svc.generate_room_wise(), "room-alias")


# -----------------------------------------------------------------
#  GET /download (legacy — redirects to overall)
# -----------------------------------------------------------------

@export_bp.route("/download", methods=["GET"])
@login_required
def download_timetable_legacy():
    """Legacy endpoint — returns the overall timetable."""
    return _download(lambda svc: svc.generate_overall(), "overall")


# -----------------------------------------------------------------
#  GET /preview – preview the timetable grid as JSON
# -----------------------------------------------------------------

@export_bp.route("/preview", methods=["GET"])
@login_required
def preview_timetable():
    """
    Return the timetable data structured as a grid (JSON),
    matching the layout that would appear in the Excel file.

    This is useful for the frontend to render a grid view
    without downloading the actual file.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        rows = db.query(Timetable).filter(Timetable.user_id == user_id).all()

        if not rows:
            return jsonify({
                "message": "No timetable data found.",
                "grid": {},
            }), 200

        # Build a grid structure: { batch_label: { time_slot: { day: cell_data } } }
        from collections import defaultdict

        grid = {}

        for row in rows:
            r = row.to_dict()
            batch = r["batch_label"]

            if batch not in grid:
                grid[batch] = {}

            start = str(r["start_time"])
            if len(start) > 5:
                start = start[:5]

            if start not in grid[batch]:
                grid[batch][start] = {}

            grid[batch][start][r["day_of_week"]] = {
                "course_code": r["course_code"],
                "course_name": r["course_name"],
                "faculty_code": r["faculty_code"],
                "classroom_name": r["classroom_name"],
                "slot_name": r["slot_name"],
            }

        return jsonify({
            "message": f"Grid preview for {len(grid)} batch(es).",
            "generated_at": max(
                (r.generated_at.isoformat() for r in rows if r.generated_at),
                default=None,
            ),
            "batches": sorted(grid.keys()),
            "grid": grid,
        }), 200

    finally:
        db.close()
