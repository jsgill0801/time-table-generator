"""
BatchCourse model (many-to-many mapping).

Links a batch to a course, recording how many students
are enrolled and which category the course falls under
for that batch (e.g. the same course can be "Core" for
one batch and "Open Elective" for another).
"""

from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from backend.db import Base


class BatchCourse(Base):
    __tablename__ = "batch_course"

    auto_id = Column(Integer, primary_key=True, autoincrement=True)

    course_id = Column(
        Integer,
        ForeignKey("course.course_id", ondelete="CASCADE"),
        nullable=False,
    )

    batch_id = Column(
        Integer,
        ForeignKey("batch.batch_id", ondelete="CASCADE"),
        nullable=False,
    )

    category_id = Column(
        Integer,
        ForeignKey("category.category_id"),
        nullable=True,
    )

    students_enrolled = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("course_id", "batch_id", name="uq_batch_course"),
        CheckConstraint("students_enrolled >= 1", name="ck_bc_enrolled"),
    )

    # Relationships
    course = relationship("Course", back_populates="batch_courses")
    batch = relationship("Batch", back_populates="batch_courses")
    category = relationship("Category")

    def __repr__(self):
        return f"<BatchCourse batch={self.batch_id} course={self.course_id}>"

    def to_dict(self):
        return {
            "auto_id": self.auto_id,
            "course_id": self.course_id,
            "batch_id": self.batch_id,
            "category_id": self.category_id,
            "students_enrolled": self.students_enrolled,
        }
