"""
Faculty model.

Represents a faculty member with their teaching constraints.
"""

from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship

from backend.db import Base


class Faculty(Base):
    __tablename__ = "faculty"

    # Faculty code is the natural primary key (e.g. "PD", "AV", "SS")
    faculty_code = Column(String(10), primary_key=True)

    faculty_name = Column(String(50), nullable=False)
    faculty_email = Column(String(100), nullable=True)

    # Maximum number of lectures this faculty can teach per week
    max_load = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("max_load >= 1", name="ck_faculty_max_load"),
    )

    # Relationships
    faculty_courses = relationship("FacultyCourse", back_populates="faculty")

    def __repr__(self):
        return f"<Faculty {self.faculty_code}: {self.faculty_name}>"

    def to_dict(self):
        return {
            "faculty_code": self.faculty_code,
            "faculty_name": self.faculty_name,
            "faculty_email": self.faculty_email,
            "max_load": self.max_load,
        }
