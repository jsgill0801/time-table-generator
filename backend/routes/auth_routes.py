"""
Authentication routes.

Provides signup, login, logout, and current-user endpoints.
Uses Flask's built-in session for server-side session management.
"""

from functools import wraps

from flask import Blueprint, request, jsonify, session
from werkzeug.security import check_password_hash

from backend.db import get_db
from backend.services.auth_service import create_user, authenticate_user
from backend.utils.errors import AuthError
from backend.models.user import User


auth_bp = Blueprint("auth", __name__)


# -----------------------------------------------------------------
#  Helper: get current user ID from session
# -----------------------------------------------------------------

def get_current_user_id():
    """
    Returns the user_id of the master admin ('admin'), so that all users share the same data.
    Should only be called after login_required decorator has verified auth.
    """
    db = next(get_db())
    try:
        master_admin = db.query(User).filter(User.username == "admin").first()
        if master_admin:
            return master_admin.user_id
    except Exception:
        pass  # nosec B110
    finally:
        db.close()
    return session.get("user_id")


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
#  Decorator: protect routes that require admin role
# -----------------------------------------------------------------

def admin_required(f):
    """
    Decorator that blocks non-admin requests.
    Requires a valid session and role == 'admin'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401

        db = next(get_db())
        try:
            user = db.query(User).filter(User.user_id == session["user_id"]).first()
            if not user:
                session.clear()
                return jsonify({"error": "User not found."}), 404
            if user.role != "admin":
                return jsonify({"error": "Admin privileges required."}), 403
        finally:
            db.close()

        return f(*args, **kwargs)
    return decorated


# -----------------------------------------------------------------
#  Decorator: protect routes that require master admin role
# -----------------------------------------------------------------

def master_admin_required(f):
    """
    Decorator that blocks non-master-admin requests.
    Requires a valid session and username == 'admin'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Authentication required."}), 401
        if session.get("username") != "admin":
            return jsonify({"error": "Master admin privileges required."}), 403
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
    master_admin_password = data.get("masterAdminPassword", "")

    if not username:
        return jsonify({"error": "Username is required."}), 400

    if not email:
        return jsonify({"error": "Email is required."}), 400

    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters."}), 400

    role = "admin"

    # Create the user
    try:
        db = next(get_db())
        existing_users = db.query(User).count()

        # If there are existing users, we require verification of the master admin password
        if existing_users > 0:
            # Find the master admin whose username is 'admin'
            master_admin = db.query(User).filter(User.username == "admin").first()
            if not master_admin:
                return jsonify({"error": "Master admin account ('admin') not found in database. Cannot verify registration."}), 400
            
            if not check_password_hash(master_admin.password_hash, master_admin_password):
                return jsonify({"error": "Invalid Master Admin password."}), 400

        user = create_user(db, username, email, password, role=role)

        return jsonify({
            "message": "Account created successfully.",
            "user": user.to_dict(),
        }), 201

    except AuthError as e:
        return jsonify({"error": str(e)}), 409

    finally:
        db.close()


# -----------------------------------------------------------------
#  GET /users – list all users (Master Admin only)
# -----------------------------------------------------------------

@auth_bp.route("/users", methods=["GET"])
@master_admin_required
def list_users():
    """List all registered users/admins."""
    db = next(get_db())
    try:
        users = db.query(User).order_by(User.user_id).all()
        return jsonify([u.to_dict() for u in users]), 200
    finally:
        db.close()


# -----------------------------------------------------------------
#  DELETE /users/<id> – delete a user (Master Admin only)
# -----------------------------------------------------------------

@auth_bp.route("/users/<int:user_id>", methods=["DELETE"])
@master_admin_required
def delete_user(user_id):
    """Delete a user/admin account."""
    db = next(get_db())
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return jsonify({"error": "User not found."}), 404

        # Prevent master admin from deleting themselves
        if user.username == "admin":
            return jsonify({"error": "The master admin account cannot be deleted."}), 400

        db.delete(user)
        db.commit()
        return jsonify({"message": "User deleted successfully."}), 200
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
