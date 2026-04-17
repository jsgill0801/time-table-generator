"""
Classroom model.

Represents a physical room where classes can be held.
"""

from sqlalchemy import Column, Integer, String, CheckConstraint

from backend.db import Base


class Classroom(Base):
    __tablename__ = "classroom"

    # Room name is the natural primary key (e.g. "LT-1", "CEP202")
    classroom_name = Column(String(10), primary_key=True)

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
