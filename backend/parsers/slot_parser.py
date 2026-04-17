"""
CSV parser for Slot records.

Expected CSV columns:
    slot_id, day_of_week, start_time, end_time, slot_name (optional)
"""

from backend.parsers.base_parser import BaseParser
from backend.utils.errors import DataError


# Valid day names for validation
VALID_DAYS = {
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday",
}


class SlotParser(BaseParser):

    REQUIRED_FIELDS = [
        "slot_id",
        "day_of_week",
        "start_time",
        "end_time",
    ]

    def validate_row(self, row: dict, row_num: int) -> dict:
        """
        Validate and clean a single slot row.

        Rules:
            - slot_id: non-empty, max 10 characters
            - day_of_week: must be a valid weekday name
            - start_time: valid HH:MM format
            - end_time: valid HH:MM format, must be after start_time
            - slot_name: optional (e.g. "Slot-1", "Free-Slot")
        """
        slot_id = self.require_non_empty(row["slot_id"], "slot_id", row_num)

        if len(slot_id) > 10:
            raise DataError("slot_id", f"Max 10 characters, got {len(slot_id)}.", row_num)

        # Validate day of week
        day = row["day_of_week"].strip().title()

        if day not in VALID_DAYS:
            raise DataError(
                "day_of_week",
                f"Must be a valid weekday (Monday-Sunday), got '{day}'.",
                row_num,
            )

        # Validate times
        start = self.parse_time(row["start_time"], "start_time", row_num)
        end = self.parse_time(row["end_time"], "end_time", row_num)

        if end <= start:
            raise DataError(
                "end_time",
                f"End time ({end}) must be after start time ({start}).",
                row_num,
            )

        # Slot name is optional
        slot_name = row.get("slot_name", "").strip() or None

        return {
            "slot_id": slot_id,
            "day_of_week": day,
            "start_time": start,
            "end_time": end,
            "slot_name": slot_name,
        }
