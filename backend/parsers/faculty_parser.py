"""
CSV parser for Faculty records.

Expected CSV columns:
    faculty_code, faculty_name, max_load, faculty_email (optional)
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


class FacultyParser(BaseParser):

    REQUIRED_FIELDS = [
        "faculty_code",
        "faculty_name",
        "max_load",
    ]

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate and clean a single faculty row.

        Rules:
            - faculty_code: non-empty, max 10 characters
            - faculty_name: non-empty
            - max_load: integer >= 1
            - faculty_email: optional, basic format check if provided
        """
        code = self.require_non_empty(row["faculty_code"], "faculty_code", row_num)

        if len(code) > 10:
            raise DataError("faculty_code", f"Max 10 characters, got {len(code)}.", row_num)

        name = self.require_non_empty(row["faculty_name"], "faculty_name", row_num)

        max_load = self.parse_int(row["max_load"], "max_load", row_num, min_val=1)

        # Email is optional
        email = row.get("faculty_email", "").strip() or None

        if email and "@" not in email:
            raise DataError(
                "faculty_email",
                f"Invalid email format: '{email}'.",
                row_num,
            )

        return {
            "faculty_code": code.upper(),
            "faculty_name": name,
            "max_load": max_load,
            "faculty_email": email,
        }
