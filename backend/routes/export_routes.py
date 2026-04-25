"""
Export routes – Excel download endpoint.

Endpoints:
    GET /download       Generate and download the timetable as an Excel file
"""

import os
import logging

from flask import Blueprint, send_file, jsonify

from backend.db import get_db
from backend.models.timetable import Timetable
from backend.services.export_service import ExportService
from backend.routes.auth_routes import login_required

logger = logging.getLogger(__name__)


export_bp = Blueprint("export", __name__)


# -----------------------------------------------------------------
#  GET /download – generate and download Excel file
# -----------------------------------------------------------------

@export_bp.route("/download", methods=["GET"])
@login_required
def download_timetable():
    """
    Generate an Excel workbook from the current timetable
    data and send it as a file download.

    Returns a .xlsx file with:
        - Master sheet (all batches)
        - Per-batch sheets
        - Faculty workload summary
    """
    db = next(get_db())
    try:
        # Fetch all timetable rows
        rows = db.query(Timetable).all()

        if not rows:
            return jsonify({
                "error": "No timetable data found",
                "message": "Run timetable generation first before downloading.",
            }), 404

        # Convert to dicts
        timetable_data = [r.to_dict() for r in rows]

        # Generate the Excel file
        service = ExportService(timetable_data)
        filepath = service.generate()

        logger.info("Excel file generated: %s", filepath)

        # Send the file as a download
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except Exception as e:
        logger.error("Excel export failed: %s", str(e))
        return jsonify({
            "error": "Export failed",
            "message": f"Failed to generate Excel file: {str(e)}",
        }), 500

    finally:
        db.close()


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
    db = next(get_db())
    try:
        rows = db.query(Timetable).all()

        if not rows:
            return jsonify({
                "message": "No timetable data found.",
                "grid": {},
            }), 200

        # Build a grid structure: { batch_label: { time_slot: { day: cell_data } } }
        from collections import defaultdict
        from backend.utils.helpers import DAY_ORDER

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
            "batches": sorted(grid.keys()),
            "grid": grid,
        }), 200

    finally:
        db.close()
