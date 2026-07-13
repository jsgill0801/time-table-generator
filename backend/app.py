"""
Flask application factory.

Creates and configures the Flask app, registers blueprints,
enables CORS, sets up error handlers, and initialises the
database tables.
"""
import os

from flask import Flask, jsonify
from flask_cors import CORS

from backend.config import DevelopmentConfig
from backend.db import init_db
from backend.utils.middleware import register_error_handlers
from backend.utils.logging_config import setup_logging

# Resolve path to frontend/static so Flask serves CSS, JS, etc.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_frontend_static = os.path.join(_project_root, "frontend", "static")


def create_app(config_class=DevelopmentConfig):
    """
    Build and return a fully configured Flask application.
    """
    # Enforce PostgreSQL unless running in testing environment
    if not getattr(config_class, "TESTING", False):
        db_url = config_class.DATABASE_URL
        if not db_url or not (db_url.startswith("postgresql://") or db_url.startswith("postgresql+psycopg://")):
            raise RuntimeError(
                "DATABASE_URL must be configured with a valid PostgreSQL connection string "
                "(e.g., postgresql://user:password@localhost:5432/dbname). SQLite is not supported."
            )

    app = Flask(__name__, static_folder=_frontend_static, static_url_path="/static")
    app.config.from_object(config_class)
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

    # Allow the frontend (running on a different port) to call the API
    CORS(app, supports_credentials=True, origins=app.config.get("ALLOWED_ORIGINS", []))

    # ------------------------------------------------------------------
    # Set up structured logging
    # ------------------------------------------------------------------
    setup_logging(app)

    # ------------------------------------------------------------------
    # Register API route blueprints
    # ------------------------------------------------------------------
    from backend.routes import register_blueprints
    register_blueprints(app)

    # ------------------------------------------------------------------
    # Register frontend page routes (serves HTML/CSS/JS)
    # ------------------------------------------------------------------
    from backend.routes.frontend_routes import frontend_bp
    app.register_blueprint(frontend_bp)

    # ------------------------------------------------------------------
    # Register global error handlers
    # ------------------------------------------------------------------
    register_error_handlers(app)

    # ------------------------------------------------------------------
    # API info endpoint (for health checks)
    # ------------------------------------------------------------------
    @app.route("/api")
    def api_info():
        return jsonify({
            "application": "Time Table Generator API",
            "version": "1.0.0",
            "status": "running",
        })

    @app.after_request
    def disable_response_cache(response):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    # ------------------------------------------------------------------
    # Create database tables on first launch
    # ------------------------------------------------------------------
    init_db()

    # ------------------------------------------------------------------
    # No auto-created users or demo data.
    #
    # Admin account is created by the first signup (if DB has no users).
    # Demo dataset is available only via the explicit admin endpoint.
    # ------------------------------------------------------------------

    return app


# ------------------------------------------------------------------
# Run the development server directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=app.config.get("DEBUG", True),
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        use_reloader=False,
    )
