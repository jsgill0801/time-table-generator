"""
Timetable model.

Each row represents one scheduled session: a specific course
assigned to a (slot, room, faculty) for a particular batch.

The table stores denormalized fields (course_code, course_name,
ltpc, category_name, batch_label, day/time info) so the Excel
writer can read rows directly without complex joins.
These fields are populated at generation time.
"""

from sqlalchemy import Column, Integer, String, Time, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.db import Base


class Timetable(Base):
    __tablename__ = "timetable"

    auto_id = Column(Integer, primary_key=True, autoincrement=True)

    # ----- Foreign keys (normalized references) -----

    batch_course_id = Column(
        Integer,
        ForeignKey("batch_course.auto_id", ondelete="CASCADE"),
        nullable=False,
    )

    faculty_code = Column(
        String(10),
        ForeignKey("faculty.faculty_code"),
        nullable=False,
    )

    classroom_name = Column(
        String(10),
        ForeignKey("classroom.classroom_name"),
        nullable=False,
    )

    slot_id = Column(
        String(10),
        ForeignKey("slot.slot_id"),
        nullable=False,
    )

    # ----- Denormalized fields (for fast Excel output) -----

    day_of_week = Column(String(10), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    slot_name = Column(String(15), nullable=True)

    course_code = Column(String(10), nullable=False)
    course_name = Column(String(100), nullable=False)
    ltpc = Column(String(15), nullable=False)            # e.g. "3-0-2-4"
    category_name = Column(String(30), nullable=True)     # e.g. "Core"
    batch_label = Column(String(50), nullable=False)      # e.g. "BTech Sem-IV (ICT + CS)"

    # ----- Uniqueness constraints (hard constraint enforcement) -----

    __table_args__ = (
        # A room cannot be double-booked in the same slot
        UniqueConstraint("classroom_name", "slot_id", name="uq_room_slot"),
        # A batch-course cannot be in two slots at once
        UniqueConstraint("slot_id", "batch_course_id", name="uq_slot_batch_course"),
    )

    # Relationships
    batch_course = relationship("BatchCourse")
    faculty = relationship("Faculty")
    classroom = relationship("Classroom")
    slot = relationship("Slot")

    def __repr__(self):
        return (
            f"<Timetable {self.course_code} | {self.day_of_week} "
            f"{self.start_time} | {self.classroom_name}>"
        )

    def to_dict(self):
        return {
            "auto_id": self.auto_id,
            "batch_course_id": self.batch_course_id,
            "faculty_code": self.faculty_code,
            "classroom_name": self.classroom_name,
            "slot_id": self.slot_id,
            "day_of_week": self.day_of_week,
            "start_time": str(self.start_time),
            "end_time": str(self.end_time),
            "slot_name": self.slot_name,
            "course_code": self.course_code,
            "course_name": self.course_name,
            "ltpc": self.ltpc,
            "category_name": self.category_name,
            "batch_label": self.batch_label,
        }
