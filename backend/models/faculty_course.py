"""
FacultyCourse model (many-to-many mapping).

Links a faculty member to a course they are assigned to teach.
A course can have multiple faculty (e.g. "SS/VS" teaching jointly),
and a faculty member can teach multiple courses.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.db import Base


class FacultyCourse(Base):
    __tablename__ = "faculty_course"

    auto_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=True)

    course_id = Column(
        Integer,
        ForeignKey("course.course_id", ondelete="CASCADE"),
        nullable=False,
    )

    faculty_code = Column(
        String(10),
        ForeignKey("faculty.faculty_code", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("course_id", "faculty_code", name="uq_faculty_course"),
    )

    # Relationships
    course = relationship("Course", back_populates="faculty_courses")
    faculty = relationship("Faculty", back_populates="faculty_courses")

    def __repr__(self):
        return f"<FacultyCourse faculty={self.faculty_code} course={self.course_id}>"

    def to_dict(self):
        return {
            "auto_id": self.auto_id,
            "course_id": self.course_id,
            "faculty_code": self.faculty_code,
        }
