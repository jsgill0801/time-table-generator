"""
CSV parser for Course records.

Expected CSV columns:
    course_code, course_name, lectures, tutorials, labs, credits
"""

from backend.parsers.base_parser import BaseParser


class CourseParser(BaseParser):

    REQUIRED_FIELDS = [
        "course_code",
        "course_name",
        "lectures",
        "tutorials",
        "labs",
        "credits",
    ]

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate and clean a single course row.

        Rules:
            - course_code: non-empty, max 10 characters
            - course_name: non-empty, max 100 characters
            - lectures, tutorials, labs: integers >= 0
            - credits: number >= 0 (can be decimal, e.g. 4.5)
            - at least one of lectures/tutorials/labs must be > 0
        """
        code = self.require_non_empty(row["course_code"], "course_code", row_num)

        if len(code) > 10:
            from backend.utils.errors import DataError
            raise DataError("course_code", f"Max 10 characters, got {len(code)}.", row_num)

        name = self.require_non_empty(row["course_name"], "course_name", row_num)

        if len(name) > 100:
            from backend.utils.errors import DataError
            raise DataError("course_name", f"Max 100 characters, got {len(name)}.", row_num)

        lectures = self.parse_int(row["lectures"], "lectures", row_num, min_val=0)
        tutorials = self.parse_int(row["tutorials"], "tutorials", row_num, min_val=0)
        labs = self.parse_int(row["labs"], "labs", row_num, min_val=0)
        credits = self.parse_float(row["credits"], "credits", row_num, min_val=0)

        # A course must have at least some contact hours
        if lectures + tutorials + labs == 0:
            from backend.utils.errors import DataError
            raise DataError(
                "lectures",
                "At least one of lectures/tutorials/labs must be greater than 0.",
                row_num,
            )

        return {
            "course_code": code.upper(),
            "course_name": name,
            "lectures": lectures,
            "tutorials": tutorials,
            "labs": labs,
            "credits": credits,
        }
