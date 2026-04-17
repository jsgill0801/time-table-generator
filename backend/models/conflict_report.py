"""
ConflictReport model.

Stores unresolved scheduling conflicts that the engine
could not place. Each row records which course/batch/faculty
could not be scheduled and why.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from backend.db import Base


class ConflictReport(Base):
    __tablename__ = "conflict_report"

    conflict_id = Column(Integer, primary_key=True, autoincrement=True)

    course_code = Column(String(10), nullable=False)
    course_name = Column(String(100), nullable=False)
    batch_label = Column(String(50), nullable=False)
    faculty_code = Column(String(10), nullable=True)

    # Detailed reason the session could not be placed
    reason = Column(Text, nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Conflict {self.course_code} - {self.batch_label}>"

    def to_dict(self):
        return {
            "conflict_id": self.conflict_id,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "batch_label": self.batch_label,
            "faculty_code": self.faculty_code,
            "reason": self.reason,
            "created_at": str(self.created_at),
        }
