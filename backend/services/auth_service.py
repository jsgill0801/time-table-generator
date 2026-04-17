"""
Authentication service.

Handles password hashing and user credential verification.
Uses Werkzeug's security utilities for bcrypt-style hashing.
"""

from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import Session

from backend.models.user import User
from backend.utils.errors import AuthError


def create_user(db: Session, username: str, email: str, password: str) -> User:
    """
    Register a new user.

    Hashes the password before storing. Raises AuthError
    if the username or email is already taken.
    """
    # Check for duplicate username
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise AuthError(f"Username '{username}' is already taken.")

    # Check for duplicate email
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise AuthError(f"Email '{email}' is already registered.")

    user = User(
        username=username,
        email=email,
        password_hash=generate_password_hash(password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(db: Session, username: str, password: str) -> User:
    """
    Verify credentials and return the User if valid.

    Raises AuthError if the username doesn't exist or
    the password is incorrect.
    """
    user = db.query(User).filter(User.username == username).first()

    if not user:
        raise AuthError("Invalid username or password.")

    if not check_password_hash(user.password_hash, password):
        raise AuthError("Invalid username or password.")

    return user
