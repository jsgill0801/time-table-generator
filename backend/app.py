"""
Flask application factory.

Creates and configures the Flask app, registers blueprints,
enables CORS, sets up error handlers, and initialises the
database tables.
"""

from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import DevelopmentConfig
from backend.db import init_db
from backend.utils.middleware import register_error_handlers
from backend.utils.logging_config import setup_logging


def create_app(config_class=DevelopmentConfig):
    """
    Build and return a fully configured Flask application.

    Args:
        config_class: Configuration class to use (default: DevelopmentConfig).

    Returns:
        Configured Flask app instance.
    """

    app = Flask(__name__)
    app.config.from_object(config_class)

    # Allow the frontend (running on a different port) to call the API
    CORS(app, supports_credentials=True)

    # ------------------------------------------------------------------
    # Set up structured logging
    # ------------------------------------------------------------------
    setup_logging(app)

    # ------------------------------------------------------------------
    # Register route blueprints
    # ------------------------------------------------------------------
    from backend.routes import register_blueprints
    register_blueprints(app)

    # ------------------------------------------------------------------
    # Register global error handlers
    # ------------------------------------------------------------------
    register_error_handlers(app)

    # ------------------------------------------------------------------
    # Root welcome route
    # ------------------------------------------------------------------
    @app.route("/")
    def index():
        return jsonify({
            "application": "Time Table Generator API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "auth": "/api/v1/auth  (signup, login, logout)",
                "courses": "/api/v1/courses",
                "batches": "/api/v1/batches",
                "faculties": "/api/v1/faculties",
                "classrooms": "/api/v1/classrooms",
                "slots": "/api/v1/slots",
                "import": "/api/v1/import",
                "generate": "/api/v1/generate",
                "timetable": "/api/v1/timetable",
                "export": "/api/v1/export  (download, preview)",
                "data": "/api/v1/data",
            },
        })

    # ------------------------------------------------------------------
    # Create database tables on first launch
    # ------------------------------------------------------------------
    #init_db()

    return app


# ------------------------------------------------------------------
# Run the development server directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
