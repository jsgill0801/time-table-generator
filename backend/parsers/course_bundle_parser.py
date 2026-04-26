"""
CSV parser for the combined course import format.

Expected CSV columns:
    course_code, course_name, lectures, tutorials, labs, credits,
    batches, faculty

The `batches` column mirrors the course input form. It accepts one or
more mappings separated by semicolons:

    Batch Label|Category
    Batch Label|Category|Students Enrolled

Example:
    BTech Sem-4 (ICT) Sec-A|Core|55;BTech Sem-4 (ICT) Sec-B|Core|50

The `faculty` column accepts either the faculty code or the faculty name.
"""

from backend.parsers.base_parser import BaseParser
from backend.parsers.course_parser import CourseParser
from backend.utils.errors import DataError


class CourseBundleParser(BaseParser):

    REQUIRED_FIELDS = [
        "course_code",
        "course_name",
        "lectures",
        "tutorials",
        "labs",
        "credits",
        "batches",
        "faculty",
    ]

    def __init__(self, known_batch_labels: set[str], faculty_lookup: dict[str, str]):
        self.known_batch_lookup = {
            self._normalize_token(label): label for label in known_batch_labels
        }
        self.faculty_lookup = {
            self._normalize_token(token): code for token, code in faculty_lookup.items()
        }
        self.course_parser = CourseParser()

    def validate_row(self, row: dict, row_num: int) -> dict:
        course_data = self.course_parser.validate_row(row, row_num)

        faculty_value = self.require_non_empty(row["faculty"], "faculty", row_num)
        faculty_code = self.faculty_lookup.get(self._normalize_token(faculty_value))

        if not faculty_code:
            raise DataError(
                "faculty",
                f"Faculty '{faculty_value}' does not exist in the loaded faculty list.",
                row_num,
            )

        batches_value = self.require_non_empty(row["batches"], "batches", row_num)
        batch_mappings = []
        seen_mappings = set()

        for raw_mapping in batches_value.split(";"):
            mapping_value = raw_mapping.strip()

            if not mapping_value:
                continue

            parts = [part.strip() for part in mapping_value.split("|")]

            if len(parts) not in (2, 3):
                raise DataError(
                    "batches",
                    "Each batches entry must use 'Batch Label|Category' or "
                    "'Batch Label|Category|Students Enrolled'.",
                    row_num,
                )

            batch_label = self.require_non_empty(parts[0], "batches", row_num)
            category_name = self.require_non_empty(parts[1], "batches", row_num)
            students_enrolled = (
                self.parse_int(parts[2], "batches", row_num, min_val=1)
                if len(parts) == 3 and parts[2]
                else 1
            )

            normalized_batch = self._normalize_token(batch_label)
            resolved_batch_label = self.known_batch_lookup.get(normalized_batch)

            if not resolved_batch_label:
                raise DataError(
                    "batches",
                    f"Batch '{batch_label}' does not exist in the loaded batch list.",
                    row_num,
                )

            mapping_key = (
                self._normalize_token(resolved_batch_label),
                self._normalize_token(category_name),
            )

            if mapping_key in seen_mappings:
                raise DataError(
                    "batches",
                    f"Duplicate batch mapping '{batch_label} | {category_name}' found.",
                    row_num,
                )

            seen_mappings.add(mapping_key)
            batch_mappings.append({
                "batch_label": resolved_batch_label,
                "category": category_name,
                "students_enrolled": students_enrolled,
            })

        if not batch_mappings:
            raise DataError(
                "batches",
                "At least one batch mapping is required.",
                row_num,
            )

        return {
            **course_data,
            "faculty_code": faculty_code,
            "batch_mappings": batch_mappings,
        }

    @staticmethod
    def _normalize_token(value: str) -> str:
        return " ".join(str(value or "").split()).casefold()
