"""
CSV parser for BatchCourse mapping records.

Expected CSV columns:
    course_code, program, branch, semester, section,
    category, students_enrolled

This parser performs foreign-key validation: it checks that
every course_code and batch combination referenced in the CSV
actually exists in the already-loaded Course and Batch datasets.
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


class BatchCourseParser(BaseParser):

    REQUIRED_FIELDS = [
        "course_code",
        "program",
        "branch",
        "semester",
        "students_enrolled",
    ]

    def __init__(self, known_course_codes: set[str], known_batches: list[dict]):
        """
        Args:
            known_course_codes: Set of valid course codes (uppercase)
                                already loaded from the courses CSV or DB.
            known_batches:      List of batch dicts, each having
                                {program, branch, semester, section}.
        """
        self.known_course_codes = known_course_codes

        # Build a set of batch identity tuples for fast lookup
        self.known_batch_keys = set()

        for b in known_batches:
            key = (
                b["program"].strip(),
                b["branch"].strip(),
                b["semester"],
                (b.get("section") or "").strip() or None,
            )
            self.known_batch_keys.add(key)

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate a batch-course mapping row.

        Rules:
            - course_code: must exist in the known courses
            - program + branch + semester + section: must match a known batch
            - students_enrolled: integer >= 1
            - category: optional (e.g. "Core", "Science Elective")
        """
        # Validate course reference
        code = self.require_non_empty(row["course_code"], "course_code", row_num).upper()

        if code not in self.known_course_codes:
            raise DataError(
                "course_code",
                f"Course '{code}' does not exist in the loaded courses. "
                f"Please check the course code or load courses first.",
                row_num,
            )

        # Validate batch reference
        program = self.require_non_empty(row["program"], "program", row_num)
        branch = self.require_non_empty(row["branch"], "branch", row_num)
        semester = self.parse_int(row["semester"], "semester", row_num, min_val=1)
        section = row.get("section", "").strip() or None

        batch_key = (program, branch, semester, section)

        if batch_key not in self.known_batch_keys:
            label = f"{program} / {branch} / Sem {semester}"
            if section:
                label += f" / Sec {section}"
            raise DataError(
                "batch",
                f"Batch ({label}) does not exist in the loaded batches.",
                row_num,
            )

        # Validate enrollment
        enrolled = self.parse_int(
            row["students_enrolled"], "students_enrolled", row_num, min_val=1
        )

        # Category is optional
        category = row.get("category", "").strip() or None

        return {
            "course_code": code,
            "program": program,
            "branch": branch,
            "semester": semester,
            "section": section,
            "students_enrolled": enrolled,
            "category": category,
        }
