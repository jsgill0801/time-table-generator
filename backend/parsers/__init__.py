"""
Parsers package.

Each parser reads a CSV file for a specific entity, validates
every row, and returns clean Python dictionaries ready to be
inserted into the database.
"""

from backend.parsers.course_parser import CourseParser
from backend.parsers.batch_parser import BatchParser
from backend.parsers.faculty_parser import FacultyParser
from backend.parsers.classroom_parser import ClassroomParser
from backend.parsers.slot_parser import SlotParser
from backend.parsers.batch_course_parser import BatchCourseParser
from backend.parsers.faculty_course_parser import FacultyCourseParser

__all__ = [
    "CourseParser",
    "BatchParser",
    "FacultyParser",
    "ClassroomParser",
    "SlotParser",
    "BatchCourseParser",
    "FacultyCourseParser",
]
