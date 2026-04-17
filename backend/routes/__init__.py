"""
Routes package.

Provides a single function to register all API blueprints
with the Flask application.
"""

from backend.routes.auth_routes import auth_bp


def register_blueprints(app):
    """Register all route blueprints under /api/v1/."""

    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

    # CRUD blueprints will be registered here as they are built:
    # app.register_blueprint(course_bp, url_prefix="/api/v1/courses")
    # app.register_blueprint(batch_bp, url_prefix="/api/v1/batches")
    # app.register_blueprint(faculty_bp, url_prefix="/api/v1/faculties")
    # app.register_blueprint(classroom_bp, url_prefix="/api/v1/classrooms")
    # app.register_blueprint(slot_bp, url_prefix="/api/v1/slots")
    # app.register_blueprint(generate_bp, url_prefix="/api/v1/generate")
