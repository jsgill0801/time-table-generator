"""
Base parser with shared CSV reading and validation logic.

All entity-specific parsers inherit from this class and
override the `validate_row` method to add their own rules.
"""

import csv
import io
from abc import ABC, abstractmethod

from backend.utils.errors import DataError


class BaseParser(ABC):
    """
    Abstract base class for CSV parsers.

    Subclasses must define:
        - REQUIRED_FIELDS: list of column names that must be present
        - validate_row(row, row_num): validate a single row and return a clean dict
    """

    REQUIRED_FIELDS: list[str] = []

    def parse(self, file_content: str) -> list[dict]:
        """
        Parse a CSV string and return a list of validated dictionaries.

        Args:
            file_content: The raw CSV text (including header row).

        Returns:
            List of cleaned, validated row dicts.

        Raises:
            DataError: If any row fails validation.
        """
        reader = csv.DictReader(io.StringIO(file_content))

        # Check that all required columns exist in the header
        if reader.fieldnames is None:
            raise DataError("CSV", "File is empty or has no header row.")

        self._check_required_columns(reader.fieldnames)

        # Parse and validate each row
        results = []

        for row_num, raw_row in enumerate(reader, start=2):
            # Strip whitespace from all values
            row = {
                key.strip(): (val.strip() if val else "")
                for key, val in raw_row.items()
                if key is not None
            }

            # Skip completely blank rows
            if all(v == "" for v in row.values()):
                continue

            # Let the subclass validate and transform this row
            validated = self.validate_row(row, row_num)
            results.append(validated)

        if not results:
            raise DataError("CSV", "File contains no data rows.")

        return results

    def parse_file(self, file_path: str) -> list[dict]:
        """
        Read a CSV file from disk and parse it.

        Args:
            file_path: Path to the CSV file.

        Returns:
            List of cleaned, validated row dicts.
        """
        with open(file_path, "r", encoding="utf-8-sig") as f:
            content = f.read()

        return self.parse(content)

    @abstractmethod
    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate a single CSV row and return a cleaned dictionary.

        Must be implemented by each entity-specific parser.

        Args:
            row:     Dict of column_name -> value for this row.
            row_num: 1-based row number (for error messages).

        Returns:
            Cleaned dict with correct types.

        Raises:
            DataError: If any field is invalid.
        """
        pass

    def _check_required_columns(self, fieldnames: list[str]):
        """Verify that all required columns are present in the CSV header."""
        header_set = {name.strip() for name in fieldnames}

        for field in self.REQUIRED_FIELDS:
            if field not in header_set:
                raise DataError(
                    field,
                    f"Required column '{field}' is missing from the CSV header. "
                    f"Found columns: {sorted(header_set)}",
                )

    # -----------------------------------------------------------------
    #  Shared validation helpers for subclasses
    # -----------------------------------------------------------------

    @staticmethod
    def require_non_empty(value: str, field: str, row_num: int) -> str:
        """Check that a string field is not empty."""
        if not value:
            raise DataError(field, "This field cannot be empty.", row_num)
        return value

    @staticmethod
    def parse_int(value: str, field: str, row_num: int, min_val=None) -> int:
        """Parse a string as an integer with optional minimum check."""
        try:
            result = int(value)
        except (ValueError, TypeError):
            raise DataError(field, f"Expected an integer, got '{value}'.", row_num)

        if min_val is not None and result < min_val:
            raise DataError(field, f"Must be at least {min_val}, got {result}.", row_num)

        return result

    @staticmethod
    def parse_float(value: str, field: str, row_num: int, min_val=None) -> float:
        """Parse a string as a float with optional minimum check."""
        try:
            result = float(value)
        except (ValueError, TypeError):
            raise DataError(field, f"Expected a number, got '{value}'.", row_num)

        if min_val is not None and result < min_val:
            raise DataError(field, f"Must be at least {min_val}, got {result}.", row_num)

        return result

    @staticmethod
    def parse_time(value: str, field: str, row_num: int) -> str:
        """
        Validate that a value looks like a time string (HH:MM or H:MM).
        Returns the normalized HH:MM format.
        """
        if not value:
            raise DataError(field, "Time cannot be empty.", row_num)

        parts = value.split(":")

        if len(parts) != 2:
            raise DataError(field, f"Expected time format HH:MM, got '{value}'.", row_num)

        try:
            hour = int(parts[0])
            minute = int(parts[1])
        except ValueError:
            raise DataError(field, f"Expected time format HH:MM, got '{value}'.", row_num)

        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise DataError(field, f"Invalid time value '{value}'.", row_num)

        return f"{hour:02d}:{minute:02d}"
