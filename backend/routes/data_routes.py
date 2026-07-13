"""
Data management routes.

Provides utility endpoints for clearing data and checking
the overall health of the loaded dataset.

All operations are scoped to the current user's data.

Endpoints:
    DELETE /all                     Clear all entity data for current user
    DELETE /timetable               Clear only the generated timetable and conflicts for current user
    GET    /counts                  Quick count of records in each table for current user
    POST   /bootstrap-admin-demo    Seed admin demo data into an empty dataset for current user
"""

from flask import Blueprint, jsonify, session

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
from backend.models.user import User
from backend.routes.auth_routes import login_required, admin_required, get_current_user_id
from backend.seed import seed_dataset
from backend.utils.errors import DataError


data_bp = Blueprint("data", __name__)


def _core_counts(db, user_id) -> dict[str, int]:
    """Return record counts for all entity tables filtered by user_id."""
    return {
        "courses": db.query(Course).filter(Course.user_id == user_id).count(),
        "batches": db.query(Batch).filter(Batch.user_id == user_id).count(),
        "faculties": db.query(Faculty).filter(Faculty.user_id == user_id).count(),
        "classrooms": db.query(Classroom).filter(Classroom.user_id == user_id).count(),
        "slots": db.query(Slot).filter(Slot.user_id == user_id).count(),
        "categories": db.query(Category).filter(Category.user_id == user_id).count(),
        "batch_courses": db.query(BatchCourse).filter(BatchCourse.user_id == user_id).count(),
        "faculty_courses": db.query(FacultyCourse).filter(FacultyCourse.user_id == user_id).count(),
        "timetable_entries": db.query(Timetable).filter(Timetable.user_id == user_id).count(),
        "conflicts": db.query(ConflictReport).filter(ConflictReport.user_id == user_id).count(),
    }


# -----------------------------------------------------------------
#  DELETE /all – clear all entity data for current user
# -----------------------------------------------------------------

@data_bp.route("/all", methods=["DELETE"])
@admin_required
def clear_all_data():
    """
    Delete all entity data for the current user from the database.

    Clears in reverse-dependency order to avoid FK violations.
    User accounts are preserved.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        # Order matters: delete children before parents
        counts = {}
        counts["timetable"] = db.query(Timetable).filter(Timetable.user_id == user_id).delete()
        counts["conflict_report"] = db.query(ConflictReport).filter(ConflictReport.user_id == user_id).delete()
        counts["faculty_course"] = db.query(FacultyCourse).filter(FacultyCourse.user_id == user_id).delete()
        counts["batch_course"] = db.query(BatchCourse).filter(BatchCourse.user_id == user_id).delete()
        counts["slot"] = db.query(Slot).filter(Slot.user_id == user_id).delete()
        counts["classroom"] = db.query(Classroom).filter(Classroom.user_id == user_id).delete()
        counts["faculty"] = db.query(Faculty).filter(Faculty.user_id == user_id).delete()
        counts["category"] = db.query(Category).filter(Category.user_id == user_id).delete()
        counts["batch"] = db.query(Batch).filter(Batch.user_id == user_id).delete()
        counts["course"] = db.query(Course).filter(Course.user_id == user_id).delete()

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
#  DELETE /timetable – clear only generated results for current user
# -----------------------------------------------------------------

@data_bp.route("/timetable", methods=["DELETE"])
@admin_required
def clear_timetable():
    """
    Delete only the generated timetable and conflict report
    for the current user, leaving all input data intact.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        tt_count = db.query(Timetable).filter(Timetable.user_id == user_id).delete()
        cr_count = db.query(ConflictReport).filter(ConflictReport.user_id == user_id).delete()

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
#  POST /bootstrap-admin-demo – seed admin demo data
# -----------------------------------------------------------------

@data_bp.route("/bootstrap-admin-demo", methods=["POST"])
@admin_required
def bootstrap_admin_demo():
    """
    Seed the bundled demo dataset for admin users.

    This route is intended for empty databases only so the admin can
    sign in and immediately test timetable generation.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        user = db.query(User).filter(User.user_id == user_id).first()

        if not user:
            session.clear()
            return jsonify({"error": "User not found."}), 404

        if user.role != "admin":
            return jsonify({"error": "Only admin users can load the demo dataset."}), 403

        counts = _core_counts(db, user_id)

        if any(counts.values()):
            return jsonify({
                "error": "Demo data can only be loaded into an empty dataset.",
                "counts": counts,
            }), 409

        seeded, total = seed_dataset(db, user_id=user_id)

        return jsonify({
            "message": f"Admin demo data loaded. {total} record(s) inserted.",
            "seeded": seeded,
            "total": total,
        }), 201

    except DataError as error:
        db.rollback()
        return jsonify({"error": str(error)}), 400
    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /counts – record counts per table for current user
# -----------------------------------------------------------------

@data_bp.route("/counts", methods=["GET"])
@login_required
def get_record_counts():
    """
    Return the number of records in each entity table for the current user.
    Useful for a quick health check or dashboard.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        counts = _core_counts(db, user_id)

        return jsonify({
            "message": "Record counts.",
            "counts": counts,
        }), 200

    finally:
        db.close()
