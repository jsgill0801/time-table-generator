"""
Timetable generation and download routes.

Handles the generation workflow:
    1. Run pre-generation validation checks
    2. If valid, trigger the scheduling engine
    3. Provide download endpoints for generated outputs

All operations are scoped to the current user's data.

Endpoints:
    POST /                  Trigger timetable generation
    GET  /validate          Run validation checks without generating
    GET  /conflicts         Retrieve the conflict report
"""

from flask import Blueprint, request, jsonify
import os
import json

from backend.db import get_db
from backend.models.timetable import Timetable
from backend.models.conflict_report import ConflictReport
from backend.services.validation_service import ValidationService
from backend.services.data_service import DataService
from backend.services.scheduler import Scheduler
from backend.services.optimiser import Optimiser
from backend.routes.auth_routes import login_required, admin_required, get_current_user_id

from datetime import datetime, time as dt_time
from collections import Counter
from collections import defaultdict


generate_bp = Blueprint("generate", __name__)
DEBUG_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "debug-ecec21.log",
)


# -----------------------------------------------------------------
#  POST / – trigger timetable generation
# -----------------------------------------------------------------

@generate_bp.route("/", methods=["POST"])
@admin_required
def generate_timetable():
    """
    Generate the timetable for the current user.

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
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        run_started = datetime.utcnow()
        run_id = f"generate_{int(run_started.timestamp() * 1000)}"
        try:
            payload = {
                "sessionId": "ecec21",
                "runId": run_id,
                "hypothesisId": "H12",
                "location": "generate_routes.py:generate_timetable",
                "message": "Entered generate_timetable route",
                "data": {"user_id": user_id},
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception:
            pass

        # Step 1: Run validation checks (user-scoped)
        validator = ValidationService(db, user_id=user_id)
        errors = validator.run_all_checks()

        if errors:
            return jsonify({
                "status": "validation_failed",
                "message": "Cannot generate timetable. Fix the following issues first.",
                "errors": errors,
            }), 400

        # Step 2: Clear previous generation results (user-scoped)
        db.query(Timetable).filter(Timetable.user_id == user_id).delete()
        db.query(ConflictReport).filter(ConflictReport.user_id == user_id).delete()
        db.commit()

        # Step 3: Fetch and preprocess all input data (user-scoped)
        data_service = DataService(db, user_id=user_id)
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

        # region agent log
        try:
            required_counter = Counter(
                (d["course_code"], d["batch_label"]) for d in demand for _ in range(d["lectures_required"])
            )
            placed_counter = Counter(
                (a["course_code"], a["batch_label"]) for a in result["assignments"]
            )
            deficits = []
            for key, required in required_counter.items():
                placed = placed_counter.get(key, 0)
                if placed < required:
                    deficits.append({
                        "course_code": key[0],
                        "batch_label": key[1],
                        "required": required,
                        "placed": placed,
                    })
            payload = {
                "sessionId": "ecec21",
                "runId": run_id,
                "hypothesisId": "H9",
                "location": "generate_routes.py:generate_timetable",
                "message": "Post-scheduler demand coverage",
                "data": {
                    "required_total": sum(required_counter.values()),
                    "placed_total": len(result["assignments"]),
                    "conflicts_total": len(result["conflicts"]),
                    "deficits": deficits[:25],
                    "conflict_reasons": [c.get("reason", "") for c in result["conflicts"][:25]],
                },
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception:
            pass
        # endregion

        # Step 5: Run the soft-constraint optimizer on placed assignments
        if result["assignments"]:
            optimiser = Optimiser(
                assignments=result["assignments"],
                slot_lookup=scheduling_input["slot_lookup"],
                slot_day_index=scheduling_input["slot_day_index"],
                room_index=scheduling_input["room_index"],
            )
            result["assignments"] = optimiser.run()

        # region agent log
        try:
            required_by_bc = {d["batch_course_id"]: int(d["lectures_required"]) for d in demand}
            placed_by_bc = Counter(a["batch_course_id"] for a in result["assignments"])
            overscheduled = []
            underscheduled = []
            for bc_id, required in required_by_bc.items():
                placed = int(placed_by_bc.get(bc_id, 0))
                if placed > required:
                    overscheduled.append({"batch_course_id": bc_id, "required": required, "placed": placed})
                elif placed < required:
                    underscheduled.append({"batch_course_id": bc_id, "required": required, "placed": placed})

            faculty_slot = Counter()
            batch_slot = Counter()
            room_slot = Counter()
            faculty_day_positions = defaultdict(lambda: defaultdict(set))
            slot_pos = {}
            for day, slot_ids in scheduling_input["slot_day_index"].items():
                for idx, slot_id in enumerate(slot_ids):
                    slot_pos[slot_id] = (day, idx)

            for a in result["assignments"]:
                sid = a["slot_id"]
                if a.get("faculty_code"):
                    faculty_slot[(a["faculty_code"], sid)] += 1
                batch_slot[(a["batch_label"], sid)] += 1
                room_slot[(a["classroom_name"], sid)] += 1
                if a.get("faculty_code") and sid in slot_pos:
                    d, p = slot_pos[sid]
                    faculty_day_positions[a["faculty_code"]][d].add(p)

            faculty_slot_violations = sum(v - 1 for v in faculty_slot.values() if v > 1)
            batch_slot_violations = sum(v - 1 for v in batch_slot.values() if v > 1)
            room_slot_violations = sum(v - 1 for v in room_slot.values() if v > 1)

            consecutive_violations = 0
            for faculty_code, day_map in faculty_day_positions.items():
                for day, pos_set in day_map.items():
                    for p in pos_set:
                        if (p + 1) in pos_set:
                            consecutive_violations += 1

            demand_students = {d["batch_course_id"]: int(d.get("students_enrolled") or 0) for d in demand}
            room_capacity = scheduling_input["room_index"]
            room_capacity_violations = 0
            for a in result["assignments"]:
                students = demand_students.get(a["batch_course_id"], 0)
                cap = int(room_capacity.get(a["classroom_name"], 0))
                if cap < students:
                    room_capacity_violations += 1

            payload = {
                "sessionId": "ecec21",
                "runId": run_id,
                "hypothesisId": "H10",
                "location": "generate_routes.py:generate_timetable",
                "message": "Post-optimiser hard-constraint audit",
                "data": {
                    "overscheduled_count": len(overscheduled),
                    "underscheduled_count": len(underscheduled),
                    "overscheduled": overscheduled[:25],
                    "underscheduled": underscheduled[:25],
                    "faculty_slot_violations": faculty_slot_violations,
                    "batch_slot_violations": batch_slot_violations,
                    "room_slot_violations": room_slot_violations,
                    "consecutive_violations": consecutive_violations,
                    "room_capacity_violations": room_capacity_violations,
                },
                "timestamp": int(datetime.utcnow().timestamp() * 1000),
            }
            with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=True) + "\n")
        except Exception:
            pass
        # endregion

        # Step 6: Save assignments to the timetable table (with user_id)
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
                user_id=user_id,
                generated_at=run_started,
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

        # Step 7: Save conflicts to the conflict_report table (with user_id)
        for c in result["conflicts"]:
            row = ConflictReport(
                user_id=user_id,
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
        scheduled_course_codes = {
            assignment["course_code"] for assignment in result["assignments"]
        }
        demanded_course_codes = {
            item["course_code"] for item in demand
        }

        return jsonify({
            "status": status,
            "message": (
                "Timetable generated successfully with no conflicts."
                if status == "success"
                else f"Timetable generated with {stats['unresolved']} unresolved conflict(s)."
            ),
            "generated_at": run_started.isoformat() + "Z",
            "stats": stats,
            "total_courses": len(demanded_course_codes),
            "scheduled_courses": len(scheduled_course_codes),
            "total_sessions": stats["total_demand"],
            "scheduled_sessions": stats["placed"],
            "conflicts_count": stats["unresolved"],
            "conflicts": [c.to_dict() for c in db.query(ConflictReport).filter(ConflictReport.user_id == user_id).all()],
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
    Run all pre-generation validation checks and return the results
    for the current user's data.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        # Run validation (user-scoped)
        validator = ValidationService(db, user_id=user_id)
        errors = validator.run_all_checks()

        # Also gather a quick data summary (user-scoped)
        data_service = DataService(db, user_id=user_id)

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
    from the most recent generation run for the current user.
    """
    user_id = get_current_user_id()
    db = next(get_db())
    try:
        conflicts = (
            db.query(ConflictReport)
            .filter(ConflictReport.user_id == user_id)
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
