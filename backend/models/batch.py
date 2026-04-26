"""
Batch model.

A batch represents a group of students identified by their
program, branch, semester, and section.
Example: BTech - CSE - Semester 4 - Section A
"""

from sqlalchemy import Column, Integer, String, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from backend.db import Base
from backend.utils.helpers import build_batch_label


class Batch(Base):
    __tablename__ = "batch"

    batch_id = Column(Integer, primary_key=True, autoincrement=True)

    program = Column(String(30), nullable=False)     # e.g. "BTech"
    branch = Column(String(30), nullable=False)      # e.g. "ICT + CS"
    semester = Column(Integer, nullable=False)        # e.g. 4
    section = Column(String(2), nullable=True)        # e.g. "A", can be null

    __table_args__ = (
        UniqueConstraint("program", "branch", "semester", "section",
                         name="uq_batch_identity"),
        CheckConstraint("semester >= 1", name="ck_batch_semester"),
    )

    # Relationships
    batch_courses = relationship("BatchCourse", back_populates="batch")

    def __repr__(self):
        return f"<Batch {self.label}>"

    @property
    def label(self):
        """Human-readable label like 'BTech Sem-IV (ICT + CS) Sec-A'."""
        return build_batch_label(
            self.program,
            self.semester,
            self.branch,
            self.section,
        )

    def to_dict(self):
        return {
            "batch_id": self.batch_id,
            "program": self.program,
            "branch": self.branch,
            "semester": self.semester,
            "section": self.section,
            "label": self.label,
        }
