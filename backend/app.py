"""
Flask application factory.

Creates and configures the Flask app, registers blueprints,
enables CORS, sets up error handlers, and initialises the
database tables.
"""

from flask import Flask
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
    # Create database tables on first launch
    # ------------------------------------------------------------------
    init_db()

    return app


# ------------------------------------------------------------------
# Run the development server directly
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
