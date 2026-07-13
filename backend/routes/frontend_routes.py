"""
Frontend routes.

Serves all HTML pages from the frontend/templates directory.
This integrates the frontend with Flask so the entire application
runs from a single ``python -m backend.app`` command.
"""

from flask import Blueprint, send_from_directory, redirect
import os

_frontend_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
)
_template_dir = _frontend_dir
_static_dir = os.path.join(_frontend_dir, "static")

frontend_bp = Blueprint("frontend", __name__)


# -----------------------------------------------------------------
#  Page routes — each maps to an HTML template
# -----------------------------------------------------------------

@frontend_bp.route("/")
def index():
    """Health check for Render."""
    return {"status": "healthy", "service": "timetable-backend"}, 200


@frontend_bp.route("/login")
@frontend_bp.route("/login.html")
def login_page():
    return send_from_directory(_template_dir, "login.html")


@frontend_bp.route("/signup")
@frontend_bp.route("/signup.html")
def signup_page():
    return send_from_directory(_template_dir, "signup.html")


@frontend_bp.route("/dashboard")
@frontend_bp.route("/dashboard.html")
def dashboard_page():
    return send_from_directory(_template_dir, "dashboard.html")


@frontend_bp.route("/courses")
@frontend_bp.route("/courses.html")
def courses_page():
    return send_from_directory(_template_dir, "courses.html")


@frontend_bp.route("/faculty")
@frontend_bp.route("/faculty.html")
def faculty_page():
    return send_from_directory(_template_dir, "faculty.html")


@frontend_bp.route("/rooms")
@frontend_bp.route("/rooms.html")
def rooms_page():
    return send_from_directory(_template_dir, "rooms.html")


@frontend_bp.route("/batches")
@frontend_bp.route("/batches.html")
def batches_page():
    return send_from_directory(_template_dir, "batches.html")


@frontend_bp.route("/categories")
@frontend_bp.route("/categories.html")
def categories_page():
    return send_from_directory(_template_dir, "categories.html")


@frontend_bp.route("/slots")
@frontend_bp.route("/slots.html")
def slots_page():
    return send_from_directory(_template_dir, "slots.html")


@frontend_bp.route("/generate")
@frontend_bp.route("/generate.html")
def generate_page():
    return send_from_directory(_template_dir, "generate.html")


@frontend_bp.route("/timetable")
@frontend_bp.route("/timetable.html")
def timetable_page():
    return send_from_directory(_template_dir, "timetable.html")


@frontend_bp.route("/result")
@frontend_bp.route("/result.html")
def result_page():
    return send_from_directory(_template_dir, "result.html")


@frontend_bp.route("/users")
@frontend_bp.route("/users.html")
def users_page():
    return send_from_directory(_template_dir, "users.html")
