"""
Models package.

Importing all models here ensures they are registered with
SQLAlchemy's Base.metadata before init_db() is called.
"""

from backend.models.user import User
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse
from backend.models.timetable import Timetable
from backend.models.conflict_report import ConflictReport

__all__ = [
    "User",
    "Course",
    "Batch",
    "Faculty",
    "Classroom",
    "Slot",
    "Category",
    "BatchCourse",
    "FacultyCourse",
    "Timetable",
    "ConflictReport",
]
