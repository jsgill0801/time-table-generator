"""
Course model.

Represents an academic course with its credit structure
following the L-T-P-C notation (Lectures, Tutorials, Labs, Credits).
"""

from sqlalchemy import Column, Integer, String, Float, CheckConstraint, ForeignKey
from sqlalchemy.orm import relationship

from backend.db import Base


class Course(Base):
    __tablename__ = "course"

    course_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("app_user.user_id", ondelete="CASCADE"), nullable=True)

    course_code = Column(String(10), nullable=False)
    course_name = Column(String(100), nullable=False)

    # L-T-P-C credit components
    lectures = Column(Integer, nullable=False)
    tutorials = Column(Integer, nullable=False)
    labs = Column(Integer, nullable=False)
    credits = Column(Float, nullable=False)

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("lectures >= 0", name="ck_course_lectures"),
        CheckConstraint("tutorials >= 0", name="ck_course_tutorials"),
        CheckConstraint("labs >= 0", name="ck_course_labs"),
        CheckConstraint("credits >= 0", name="ck_course_credits"),
    )

    # Relationships (back-populated by BatchCourse and FacultyCourse)
    batch_courses = relationship("BatchCourse", back_populates="course")
    faculty_courses = relationship("FacultyCourse", back_populates="course")

    def __repr__(self):
        return f"<Course {self.course_code}: {self.course_name}>"

    def to_dict(self):
        return {
            "course_id": self.course_id,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "lectures": self.lectures,
            "tutorials": self.tutorials,
            "labs": self.labs,
            "credits": self.credits,
            "ltpc": f"{self.lectures}-{self.tutorials}-{self.labs}-{self.credits}",
        }
