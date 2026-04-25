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
from backend.services.scheduler import Scheduler
from backend.services.optimiser import Optimiser
from backend.routes.auth_routes import login_required

from datetime import time as dt_time


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
        5. Run the hard-constraint scheduler
        6. Run the soft-constraint optimizer
        7. Save results to database
        8. Return the result summary
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

        demand = scheduling_input["demand"]
        if not demand:
            return jsonify({
                "status": "error",
                "message": "No courses to schedule. Add batch-course mappings first.",
            }), 400

        # Step 4: Run the hard-constraint scheduler
        scheduler = Scheduler(scheduling_input)
        result = scheduler.run()

        # Step 5: Run the soft-constraint optimizer on placed assignments
        if result["assignments"]:
            optimiser = Optimiser(
                assignments=result["assignments"],
                slot_lookup=scheduling_input["slot_lookup"],
                slot_day_index=scheduling_input["slot_day_index"],
                room_index=scheduling_input["room_index"],
            )
            result["assignments"] = optimiser.run()

        # Step 6: Save assignments to the timetable table
        for a in result["assignments"]:
            # Convert time strings back to time objects if needed
            start = a["start_time"]
            end = a["end_time"]

            if isinstance(start, str):
                parts = start.split(":")
                start = dt_time(int(parts[0]), int(parts[1]))
            if isinstance(end, str):
                parts = end.split(":")
                end = dt_time(int(parts[0]), int(parts[1]))

            row = Timetable(
                batch_course_id=a["batch_course_id"],
                faculty_code=a["faculty_code"],
                classroom_name=a["classroom_name"],
                slot_id=a["slot_id"],
                day_of_week=a["day_of_week"],
                start_time=start,
                end_time=end,
                slot_name=a["slot_name"],
                course_code=a["course_code"],
                course_name=a["course_name"],
                ltpc=a["ltpc"],
                category_name=a["category_name"],
                batch_label=a["batch_label"],
            )
            db.add(row)

        # Step 7: Save conflicts to the conflict_report table
        for c in result["conflicts"]:
            row = ConflictReport(
                course_code=c["course_code"],
                course_name=c["course_name"],
                batch_label=c["batch_label"],
                faculty_code=c["faculty_code"],
                reason=c["reason"],
            )
            db.add(row)

        db.commit()

        # Step 8: Return summary
        stats = result["stats"]
        status = "success" if stats["unresolved"] == 0 else "partial"

        return jsonify({
            "status": status,
            "message": (
                "Timetable generated successfully with no conflicts."
                if status == "success"
                else f"Timetable generated with {stats['unresolved']} unresolved conflict(s)."
            ),
            "stats": stats,
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
