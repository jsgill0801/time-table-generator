"""
Authentication routes.

Provides signup, login, logout, and current-user endpoints.
Uses Flask's built-in session for server-side session management.
"""

from functools import wraps

from flask import Blueprint, request, jsonify, session

from backend.db import get_db
from backend.services.auth_service import create_user, authenticate_user
from backend.utils.errors import AuthError


auth_bp = Blueprint("auth", __name__)


# -----------------------------------------------------------------
#  Decorator: protect routes that require login
# -----------------------------------------------------------------

def login_required(f):
    """
    Decorator that blocks unauthenticated requests.
    Returns 401 if no valid session exists.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401
        return f(*args, **kwargs)
    return decorated


# -----------------------------------------------------------------
#  POST /signup – register a new user
# -----------------------------------------------------------------

@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Create a new user account."""

    data = request.get_json()

    # Validate required fields
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")

    if not username:
        return jsonify({"error": "Username is required."}), 400

    if not email:
        return jsonify({"error": "Email is required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    # Create the user
    try:
        db = next(get_db())
        user = create_user(db, username, email, password)

        return jsonify({
            "message": "Account created successfully.",
            "user": user.to_dict(),
        }), 201

    except AuthError as e:
        return jsonify({"error": str(e)}), 409

    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /login – authenticate and start a session
# -----------------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():
    """Log in with username and password."""

    data = request.get_json()

    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    try:
        db = next(get_db())
        user = authenticate_user(db, username, password)

        # Store user info in the server-side session
        session["user_id"] = user.user_id
        session["username"] = user.username

        return jsonify({
            "message": "Logged in successfully.",
            "user": user.to_dict(),
        }), 200

    except AuthError as e:
        return jsonify({"error": str(e)}), 401

    finally:
        db.close()


# -----------------------------------------------------------------
#  POST /logout – end the session
# -----------------------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Log out the current user."""

    session.clear()

    return jsonify({"message": "Logged out successfully."}), 200


# -----------------------------------------------------------------
#  GET /me – get the currently logged-in user
# -----------------------------------------------------------------

@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """Return info about the currently authenticated user."""

    db = next(get_db())

    try:
        from backend.models.user import User
        user = db.query(User).filter(User.user_id == session["user_id"]).first()

        if not user:
            session.clear()
            return jsonify({"error": "User not found."}), 404

        return jsonify({"user": user.to_dict()}), 200

    finally:
        db.close()
