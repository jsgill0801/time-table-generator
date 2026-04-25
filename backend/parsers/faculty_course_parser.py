"""
CSV parser for FacultyCourse mapping records.

Expected CSV columns:
    faculty_code, course_code

This parser performs foreign-key validation: it checks that
every faculty_code and course_code referenced in the CSV
actually exists in the already-loaded Faculty and Course datasets.
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


class FacultyCourseParser(BaseParser):

    REQUIRED_FIELDS = [
        "faculty_code",
        "course_code",
    ]

    def __init__(self, known_faculty_codes: set[str], known_course_codes: set[str]):
        """
        Args:
            known_faculty_codes: Set of valid faculty codes (uppercase)
                                 already loaded from the faculty CSV or DB.
            known_course_codes:  Set of valid course codes (uppercase)
                                 already loaded from the courses CSV or DB.
        """
        self.known_faculty_codes = known_faculty_codes
        self.known_course_codes = known_course_codes

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate a faculty-course mapping row.

        Rules:
            - faculty_code: must exist in the known faculty
            - course_code: must exist in the known courses
        """
        # Validate faculty reference
        faculty_code = self.require_non_empty(
            row["faculty_code"], "faculty_code", row_num
        ).upper()

        if faculty_code not in self.known_faculty_codes:
            raise DataError(
                "faculty_code",
                f"Faculty '{faculty_code}' does not exist in the loaded faculty list. "
                f"Please check the code or load faculty data first.",
                row_num,
            )

        # Validate course reference
        course_code = self.require_non_empty(
            row["course_code"], "course_code", row_num
        ).upper()

        if course_code not in self.known_course_codes:
            raise DataError(
                "course_code",
                f"Course '{course_code}' does not exist in the loaded courses. "
                f"Please check the code or load courses first.",
                row_num,
            )

        return {
            "faculty_code": faculty_code,
            "course_code": course_code,
        }
