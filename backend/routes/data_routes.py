"""
Data management routes.

Provides utility endpoints for clearing data and checking
the overall health of the loaded dataset.

Endpoints:
    DELETE /all              Clear all entity data (keep users)
    DELETE /timetable        Clear only the generated timetable and conflicts
    GET    /counts           Quick count of records in each table
"""

from flask import Blueprint, jsonify

from backend.db import get_db
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse
from backend.models.timetable import Timetable
from backend.models.conflict_report import ConflictReport
from backend.routes.auth_routes import login_required


data_bp = Blueprint("data", __name__)


# -----------------------------------------------------------------
#  DELETE /all – clear all entity data
# -----------------------------------------------------------------

@data_bp.route("/all", methods=["DELETE"])
@login_required
def clear_all_data():
    """
    Delete all entity data from the database.

    Clears in reverse-dependency order to avoid FK violations.
    User accounts are preserved.
    """
    db = next(get_db())
    try:
        # Order matters: delete children before parents
        counts = {}
        counts["timetable"] = db.query(Timetable).delete()
        counts["conflict_report"] = db.query(ConflictReport).delete()
        counts["faculty_course"] = db.query(FacultyCourse).delete()
        counts["batch_course"] = db.query(BatchCourse).delete()
        counts["slot"] = db.query(Slot).delete()
        counts["classroom"] = db.query(Classroom).delete()
        counts["faculty"] = db.query(Faculty).delete()
        counts["category"] = db.query(Category).delete()
        counts["batch"] = db.query(Batch).delete()
        counts["course"] = db.query(Course).delete()

        db.commit()

        total = sum(counts.values())

        return jsonify({
            "message": f"Cleared {total} record(s) across all tables.",
            "deleted": counts,
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to clear data: {str(e)}"}), 500
    finally:
        db.close()


# -----------------------------------------------------------------
#  DELETE /timetable – clear only generated results
# -----------------------------------------------------------------

@data_bp.route("/timetable", methods=["DELETE"])
@login_required
def clear_timetable():
    """
    Delete only the generated timetable and conflict report,
    leaving all input data intact.
    """
    db = next(get_db())
    try:
        tt_count = db.query(Timetable).delete()
        cr_count = db.query(ConflictReport).delete()

        db.commit()

        return jsonify({
            "message": f"Cleared {tt_count} timetable row(s) and {cr_count} conflict(s).",
            "deleted": {
                "timetable": tt_count,
                "conflict_report": cr_count,
            },
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({"error": f"Failed to clear timetable: {str(e)}"}), 500
    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /counts – record counts per table
# -----------------------------------------------------------------

@data_bp.route("/counts", methods=["GET"])
@login_required
def get_record_counts():
    """
    Return the number of records in each entity table.
    Useful for a quick health check or dashboard.
    """
    db = next(get_db())
    try:
        counts = {
            "courses": db.query(Course).count(),
            "batches": db.query(Batch).count(),
            "faculties": db.query(Faculty).count(),
            "classrooms": db.query(Classroom).count(),
            "slots": db.query(Slot).count(),
            "categories": db.query(Category).count(),
            "batch_courses": db.query(BatchCourse).count(),
            "faculty_courses": db.query(FacultyCourse).count(),
            "timetable_entries": db.query(Timetable).count(),
            "conflicts": db.query(ConflictReport).count(),
        }

        return jsonify({
            "message": "Record counts.",
            "counts": counts,
        }), 200

    finally:
        db.close()
