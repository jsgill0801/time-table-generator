"""
Routes package.

Provides a single function to register all API blueprints
with the Flask application.
"""

from backend.routes.auth_routes import auth_bp
from backend.routes.course_routes import course_bp
from backend.routes.batch_routes import batch_bp
from backend.routes.faculty_routes import faculty_bp
from backend.routes.classroom_routes import classroom_bp
from backend.routes.slot_routes import slot_bp
from backend.routes.category_routes import category_bp
from backend.routes.batch_course_routes import batch_course_bp
from backend.routes.faculty_course_routes import faculty_course_bp
from backend.routes.import_routes import import_bp
from backend.routes.generate_routes import generate_bp
from backend.routes.timetable_routes import timetable_bp
from backend.routes.data_routes import data_bp
from backend.routes.export_routes import export_bp


def register_blueprints(app):
    """Register all route blueprints under /api/v1/."""

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(course_bp, url_prefix="/api/v1/courses")
    app.register_blueprint(batch_bp, url_prefix="/api/v1/batches")
    app.register_blueprint(faculty_bp, url_prefix="/api/v1/faculties")
    app.register_blueprint(classroom_bp, url_prefix="/api/v1/classrooms")
    app.register_blueprint(slot_bp, url_prefix="/api/v1/slots")
    app.register_blueprint(category_bp, url_prefix="/api/v1/categories")
    app.register_blueprint(batch_course_bp, url_prefix="/api/v1/batch-courses")
    app.register_blueprint(faculty_course_bp, url_prefix="/api/v1/faculty-courses")
    app.register_blueprint(import_bp, url_prefix="/api/v1/import")
    app.register_blueprint(generate_bp, url_prefix="/api/v1/generate")
    app.register_blueprint(timetable_bp, url_prefix="/api/v1/timetable")
    app.register_blueprint(data_bp, url_prefix="/api/v1/data")
    app.register_blueprint(export_bp, url_prefix="/api/v1/export")
