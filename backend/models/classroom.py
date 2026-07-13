"""
Classroom model.

Represents a physical room where classes can be held.
"""

from sqlalchemy import Column, Integer, String, CheckConstraint, ForeignKey

from backend.db import Base


class Classroom(Base):
    __tablename__ = "classroom"

    classroom_name = Column(String(10), primary_key=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=True)

    # Maximum number of students the room can hold
    capacity = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("capacity >= 1", name="ck_classroom_capacity"),
    )

    def __repr__(self):
        return f"<Classroom {self.classroom_name} (cap: {self.capacity})>"

    def to_dict(self):
        return {
            "classroom_name": self.classroom_name,
            "capacity": self.capacity,
        }
