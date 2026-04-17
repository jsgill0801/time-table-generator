"""
CSV parser for Batch records.

Expected CSV columns:
    program, branch, semester, section
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


class BatchParser(BaseParser):

    REQUIRED_FIELDS = [
        "program",
        "branch",
        "semester",
    ]

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate and clean a single batch row.

        Rules:
            - program: non-empty (e.g. "BTech")
            - branch: non-empty (e.g. "ICT + CS", "MnC")
            - semester: integer >= 1
            - section: optional (e.g. "A", "B", or blank)
        """
        program = self.require_non_empty(row["program"], "program", row_num)
        branch = self.require_non_empty(row["branch"], "branch", row_num)
        semester = self.parse_int(row["semester"], "semester", row_num, min_val=1)

        # Section is optional — some batches don't have sections
        section = row.get("section", "").strip() or None

        if section and len(section) > 2:
            raise DataError("section", f"Max 2 characters, got '{section}'.", row_num)

        return {
            "program": program,
            "branch": branch,
            "semester": semester,
            "section": section,
        }
