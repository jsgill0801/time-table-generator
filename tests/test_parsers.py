"""
Tests for all CSV parser modules.

Covers:
    - CourseParser
    - BatchParser
    - FacultyParser
    - ClassroomParser
    - SlotParser
    - BatchCourseParser (with FK validation)
    - FacultyCourseParser (with FK validation)
"""

import pytest

from backend.parsers.course_parser import CourseParser
from backend.parsers.batch_parser import BatchParser
from backend.parsers.faculty_parser import FacultyParser
from backend.parsers.classroom_parser import ClassroomParser
from backend.parsers.slot_parser import SlotParser
from backend.parsers.batch_course_parser import BatchCourseParser
from backend.parsers.faculty_course_parser import FacultyCourseParser
from backend.utils.errors import DataError


# =================================================================
#  CourseParser
# =================================================================

class TestCourseParser:
    """Tests for the CourseParser."""

    def test_valid_csv(self, valid_course_csv):
        parser = CourseParser()
        rows = parser.parse(valid_course_csv)

        assert len(rows) == 2
        assert rows[0]["course_code"] == "IT205"
        assert rows[0]["course_name"] == "Data Structures"
        assert rows[0]["lectures"] == 3
        assert rows[0]["tutorials"] == 0
        assert rows[0]["labs"] == 0
        assert rows[0]["credits"] == 3.0

    def test_second_row_values(self, valid_course_csv):
        parser = CourseParser()
        rows = parser.parse(valid_course_csv)

        assert rows[1]["course_code"] == "MA206"
        assert rows[1]["tutorials"] == 1
        assert rows[1]["credits"] == 4.0

    def test_missing_required_field(self):
        csv = "course_code,course_name,lectures,tutorials,labs\nIT205,Data Structures,3,0,0\n"
        parser = CourseParser()

        with pytest.raises(DataError):
            parser.parse(csv)

    def test_invalid_numeric_field(self):
        csv = (
            "course_code,course_name,lectures,tutorials,labs,credits\n"
            "IT205,Data Structures,abc,0,0,3\n"
        )
        parser = CourseParser()

        with pytest.raises(DataError):
            parser.parse(csv)

    def test_empty_csv(self):
        csv = "course_code,course_name,lectures,tutorials,labs,credits\n"
        parser = CourseParser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  BatchParser
# =================================================================

class TestBatchParser:
    """Tests for the BatchParser."""

    def test_valid_csv(self, valid_batch_csv):
        parser = BatchParser()
        rows = parser.parse(valid_batch_csv)

        assert len(rows) == 2
        assert rows[0]["program"] == "BTech"
        assert rows[0]["branch"] == "ICT"
        assert rows[0]["semester"] == 4
        assert rows[0]["section"] == "A"

    def test_empty_section(self, valid_batch_csv):
        parser = BatchParser()
        rows = parser.parse(valid_batch_csv)

        # The second row has an empty section
        assert rows[1]["section"] is None or rows[1]["section"] == ""

    def test_missing_program(self):
        csv = "branch,semester,section\nICT,4,A\n"
        parser = BatchParser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  FacultyParser
# =================================================================

class TestFacultyParser:
    """Tests for the FacultyParser."""

    def test_valid_csv(self, valid_faculty_csv):
        parser = FacultyParser()
        rows = parser.parse(valid_faculty_csv)

        assert len(rows) == 2
        assert rows[0]["faculty_code"] == "PD"
        assert rows[0]["faculty_name"] == "Prof. Divya"
        assert rows[0]["max_load"] == 12
        assert rows[0]["faculty_email"] == "divya@test.edu"

    def test_optional_email(self, valid_faculty_csv):
        parser = FacultyParser()
        rows = parser.parse(valid_faculty_csv)

        # Second faculty has no email
        assert rows[1]["faculty_email"] is None or rows[1]["faculty_email"] == ""

    def test_invalid_max_load(self):
        csv = (
            "faculty_code,faculty_name,max_load,faculty_email\n"
            "PD,Prof. Divya,abc,divya@test.edu\n"
        )
        parser = FacultyParser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  ClassroomParser
# =================================================================

class TestClassroomParser:
    """Tests for the ClassroomParser."""

    def test_valid_csv(self, valid_classroom_csv):
        parser = ClassroomParser()
        rows = parser.parse(valid_classroom_csv)

        assert len(rows) == 2
        assert rows[0]["classroom_name"] == "LT-1"
        assert rows[0]["capacity"] == 200
        assert rows[1]["classroom_name"] == "CEP108"
        assert rows[1]["capacity"] == 60

    def test_missing_capacity(self):
        csv = "classroom_name\nLT-1\n"
        parser = ClassroomParser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  SlotParser
# =================================================================

class TestSlotParser:
    """Tests for the SlotParser."""

    def test_valid_csv(self, valid_slot_csv):
        parser = SlotParser()
        rows = parser.parse(valid_slot_csv)

        assert len(rows) == 2
        assert rows[0]["slot_id"] == "MON-0800"
        assert rows[0]["day_of_week"] == "Monday"
        assert rows[0]["start_time"] == "08:00"
        assert rows[0]["slot_name"] == "Slot-1"

    def test_missing_day_of_week(self):
        csv = "slot_id,start_time,end_time,slot_name\nMON-0800,8:00,8:50,Slot-1\n"
        parser = SlotParser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  BatchCourseParser
# =================================================================

class TestBatchCourseParser:
    """Tests for the BatchCourseParser with FK validation."""

    def _get_parser(self):
        """Return a parser with known entities for FK checking."""
        known_courses = {"IT205", "MA206"}
        known_batches = [
            {"program": "BTech", "branch": "ICT", "semester": 4, "section": "A"},
        ]
        return BatchCourseParser(known_courses, known_batches)

    def test_valid_csv(self, valid_batch_course_csv):
        parser = self._get_parser()
        rows = parser.parse(valid_batch_course_csv)

        assert len(rows) == 1
        assert rows[0]["course_code"] == "IT205"
        assert rows[0]["category"] == "Core"
        assert rows[0]["students_enrolled"] == 55

    def test_unknown_course_code(self):
        csv = (
            "course_code,program,branch,semester,section,category,students_enrolled\n"
            "UNKNOWN,BTech,ICT,4,A,Core,55\n"
        )
        parser = self._get_parser()

        with pytest.raises(DataError):
            parser.parse(csv)

    def test_unknown_batch(self):
        csv = (
            "course_code,program,branch,semester,section,category,students_enrolled\n"
            "IT205,MTech,CS,2,,Core,30\n"
        )
        parser = self._get_parser()

        with pytest.raises(DataError):
            parser.parse(csv)


# =================================================================
#  FacultyCourseParser
# =================================================================

class TestFacultyCourseParser:
    """Tests for the FacultyCourseParser with FK validation."""

    def _get_parser(self):
        """Return a parser with known entities for FK checking."""
        known_faculty = {"PD", "AV"}
        known_courses = {"IT205", "MA206"}
        return FacultyCourseParser(known_faculty, known_courses)

    def test_valid_csv(self, valid_faculty_course_csv):
        parser = self._get_parser()
        rows = parser.parse(valid_faculty_course_csv)

        assert len(rows) == 1
        assert rows[0]["faculty_code"] == "PD"
        assert rows[0]["course_code"] == "IT205"

    def test_unknown_faculty(self):
        csv = "faculty_code,course_code\nUNKNOWN,IT205\n"
        parser = self._get_parser()

        with pytest.raises(DataError):
            parser.parse(csv)

    def test_unknown_course(self):
        csv = "faculty_code,course_code\nPD,UNKNOWN\n"
        parser = self._get_parser()

        with pytest.raises(DataError):
            parser.parse(csv)
