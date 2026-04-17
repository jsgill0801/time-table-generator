"""
CSV parser for Classroom records.

Expected CSV columns:
    classroom_name, capacity
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


class ClassroomParser(BaseParser):

    REQUIRED_FIELDS = [
        "classroom_name",
        "capacity",
    ]

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate and clean a single classroom row.

        Rules:
            - classroom_name: non-empty, max 10 characters
            - capacity: integer >= 1
        """
        name = self.require_non_empty(row["classroom_name"], "classroom_name", row_num)

        if len(name) > 10:
            raise DataError("classroom_name", f"Max 10 characters, got {len(name)}.", row_num)

        capacity = self.parse_int(row["capacity"], "capacity", row_num, min_val=1)

        return {
            "classroom_name": name.upper(),
            "capacity": capacity,
        }
