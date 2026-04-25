"""
Error handling middleware for the Flask application.

Registers global error handlers that convert exceptions
into consistent JSON responses, so the frontend always
receives a predictable format.
"""

from flask import jsonify

from backend.utils.errors import DataError, ValidationError, AuthError


def register_error_handlers(app):
    """
    Register global exception handlers on the Flask app.

    This should be called during app creation (in create_app)
    after all blueprints are registered.
    """

    @app.errorhandler(DataError)
    def handle_data_error(error):
        """Return 400 for invalid input data."""
        return jsonify({
            "error": "Invalid data",
            "message": str(error),
            "field": error.field,
            "row": error.row,
        }), 400

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Return 400 for validation failures."""
        return jsonify({
            "error": "Validation failed",
            "message": str(error),
            "errors": error.errors,
        }), 400

    @app.errorhandler(AuthError)
    def handle_auth_error(error):
        """Return 401 for authentication failures."""
        return jsonify({
            "error": "Authentication failed",
            "message": str(error),
        }), 401

    @app.errorhandler(404)
    def handle_not_found(error):
        """Return 404 for unknown routes."""
        return jsonify({
            "error": "Not found",
            "message": "The requested resource was not found.",
        }), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Return 405 for unsupported HTTP methods."""
        return jsonify({
            "error": "Method not allowed",
            "message": "This HTTP method is not supported for this endpoint.",
        }), 405

    @app.errorhandler(500)
    def handle_internal_error(error):
        """Return 500 for unexpected server errors."""
        return jsonify({
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later.",
        }), 500
