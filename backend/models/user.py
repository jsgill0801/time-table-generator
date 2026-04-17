"""
User model for authentication.
"""

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from backend.db import Base


class User(Base):
    __tablename__ = "app_user"

    user_id = Column(Integer, primary_key=True, autoincrement=True)

    username = Column(String(30), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)

    # Role can be 'admin' or extended later
    role = Column(String(10), nullable=False, default="admin")

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<User {self.username}>"

    def to_dict(self):
        """Return a safe dictionary (no password hash)."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "created_at": str(self.created_at),
        }
