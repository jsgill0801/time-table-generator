"""
Timetable generation and download routes.

Handles the generation workflow:
    1. Run pre-generation validation checks
    2. If valid, trigger the scheduling engine
    3. Provide download endpoints for generated outputs

Endpoints:
    POST /                  Trigger timetable generation
    GET  /validate          Run validation checks without generating
    GET  /conflicts         Retrieve the conflict report
"""

from flask import Blueprint, request, jsonify

from backend.db import get_db
from backend.models.timetable import Timetable
from backend.models.conflict_report import ConflictReport
from backend.services.validation_service import ValidationService
from backend.services.data_service import DataService
from backend.routes.auth_routes import login_required


generate_bp = Blueprint("generate", __name__)


# -----------------------------------------------------------------
#  POST / – trigger timetable generation
# -----------------------------------------------------------------

@generate_bp.route("/", methods=["POST"])
@login_required
def generate_timetable():
    """
    Generate the timetable.

    Steps:
        1. Run all validation checks
        2. If errors exist, return them and halt
        3. Clear any previous timetable and conflict data
        4. Fetch and preprocess input data
        5. Run the scheduling engine (to be implemented)
        6. Return the result summary
    """
    db = next(get_db())
    try:
        # Step 1: Run validation checks
        validator = ValidationService(db)
        errors = validator.run_all_checks()

        if errors:
            return jsonify({
                "status": "validation_failed",
                "message": "Cannot generate timetable. Fix the following issues first.",
                "errors": errors,
            }), 400

        # Step 2: Clear previous generation results
        db.query(Timetable).delete()
        db.query(ConflictReport).delete()
        db.commit()

        # Step 3: Fetch and preprocess all input data
        data_service = DataService(db)
        scheduling_input = data_service.get_scheduling_input()

        # Quick sanity check on the preprocessed data
        demand = scheduling_input["demand"]
        if not demand:
            return jsonify({
                "status": "error",
                "message": "No courses to schedule. Add batch-course mappings first.",
            }), 400

        # Step 4: Run the scheduling engine
        # The scheduler module will be implemented separately.
        # For now, return a summary of what would be scheduled.

        total_lectures = sum(d["lectures_required"] for d in demand)
        total_rooms = len(scheduling_input["room_index"])
        total_slots = len(scheduling_input["all_slots"])

        return jsonify({
            "status": "ready",
            "message": (
                "Validation passed. Scheduling engine not yet implemented. "
                "Data is preprocessed and ready."
            ),
            "summary": {
                "courses_to_schedule": len(demand),
                "total_lectures": total_lectures,
                "available_rooms": total_rooms,
                "available_slots": total_slots,
                "faculty_count": len(scheduling_input["faculty_load"]),
            },
        }), 200

    except Exception as e:
        db.rollback()
        return jsonify({
            "status": "error",
            "message": f"Generation failed: {str(e)}",
        }), 500
    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /validate – run checks without generating
# -----------------------------------------------------------------

@generate_bp.route("/validate", methods=["GET"])
@login_required
def validate_data():
    """
    Run all pre-generation validation checks and return the results.

    This lets the user check for issues before triggering
    a full generation run.

    Returns:
        - status: "valid" or "invalid"
        - errors: list of issues found (empty if valid)
        - summary: data counts for quick overview
    """
    db = next(get_db())
    try:
        # Run validation
        validator = ValidationService(db)
        errors = validator.run_all_checks()

        # Also gather a quick data summary
        data_service = DataService(db)

        courses = data_service.fetch_courses()
        batches = data_service.fetch_batches()
        faculties = data_service.fetch_faculties()
        classrooms = data_service.fetch_classrooms()
        slots = data_service.fetch_slots()
        batch_courses = data_service.fetch_batch_courses()
        faculty_courses = data_service.fetch_faculty_courses()

        summary = {
            "courses": len(courses),
            "batches": len(batches),
            "faculties": len(faculties),
            "classrooms": len(classrooms),
            "slots": len(slots),
            "batch_course_mappings": len(batch_courses),
            "faculty_course_mappings": len(faculty_courses),
        }

        if errors:
            return jsonify({
                "status": "invalid",
                "errors": errors,
                "summary": summary,
            }), 200

        return jsonify({
            "status": "valid",
            "message": "All checks passed. Ready to generate.",
            "errors": [],
            "summary": summary,
        }), 200

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /conflicts – retrieve the conflict report
# -----------------------------------------------------------------

@generate_bp.route("/conflicts", methods=["GET"])
@login_required
def get_conflicts():
    """
    Return the list of unresolved scheduling conflicts
    from the most recent generation run.
    """
    db = next(get_db())
    try:
        conflicts = (
            db.query(ConflictReport)
            .order_by(ConflictReport.conflict_id)
            .all()
        )

        if not conflicts:
            return jsonify({
                "message": "No conflicts found. Either the timetable is fully resolved "
                           "or generation has not been run yet.",
                "conflicts": [],
            }), 200

        return jsonify({
            "message": f"{len(conflicts)} unresolved conflict(s) found.",
            "conflicts": [c.to_dict() for c in conflicts],
        }), 200

    finally:
        db.close()
