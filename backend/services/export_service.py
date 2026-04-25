"""
Excel export service.

Converts the generated timetable data into an Excel workbook
matching the university's Lecture Time Table format.

Generates three types of sheets:
    1. Master sheet (all batches combined, slot-based grid)
    2. Per-batch sheets (one sheet per batch label)
    3. Faculty workload summary sheet

The university format uses a grid layout:
    Rows    = time slots (08:00–08:50, 09:00–09:50, ...)
    Columns = days of the week (Monday–Friday)
    Cells   = course code + faculty code + room

Usage:
    from backend.services.export_service import ExportService

    service = ExportService(timetable_rows)
    filepath = service.generate()  # returns path to the .xlsx file
"""

import os
import logging
from collections import defaultdict
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import (
    Font, Alignment, Border, Side, PatternFill, NamedStyle,
)
from openpyxl.utils import get_column_letter

from backend.utils.helpers import DAY_ORDER

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------
#  Output directory
# -----------------------------------------------------------------
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "output",
)


# -----------------------------------------------------------------
#  Style constants
# -----------------------------------------------------------------
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
SUBHEADER_FILL = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
SUBHEADER_FONT = Font(name="Calibri", size=10, bold=True, color="1F4E79")
CELL_FONT = Font(name="Calibri", size=10)
TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1F4E79")
FREE_FILL = PatternFill(start_color="E8E8E8", end_color="E8E8E8", fill_type="solid")
BORDER = Border(
    left=Side(style="thin"),
    right=Side(style="thin"),
    top=Side(style="thin"),
    bottom=Side(style="thin"),
)
CENTER_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT_ALIGN = Alignment(horizontal="left", vertical="center", wrap_text=True)

# Days to include in the grid
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]


class ExportService:
    """
    Generates a styled Excel workbook from timetable data.

    Usage:
        service = ExportService(timetable_rows)
        filepath = service.generate()
    """

    def __init__(self, timetable_rows: list[dict]):
        """
        Args:
            timetable_rows: List of dicts from Timetable.to_dict().
        """
        self.rows = timetable_rows

        # Organise rows by batch_label
        self.by_batch = defaultdict(list)
        for row in self.rows:
            self.by_batch[row["batch_label"]].append(row)

        # Collect all unique time slots and sort them
        self.time_slots = self._extract_time_slots()

        # Ensure the output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def generate(self) -> str:
        """
        Generate the Excel workbook and save it to disk.

        Returns:
            Absolute path to the generated .xlsx file.
        """
        wb = Workbook()

        # Remove the default sheet
        wb.remove(wb.active)

        # Sheet 1: Master grid (all batches)
        self._write_master_sheet(wb)

        # Sheet 2..N: One sheet per batch
        for batch_label in sorted(self.by_batch.keys()):
            self._write_batch_sheet(wb, batch_label)

        # Sheet N+1: Faculty workload summary
        self._write_faculty_sheet(wb)

        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Lecture_Time_Table_{timestamp}.xlsx"
        filepath = os.path.join(OUTPUT_DIR, filename)

        wb.save(filepath)
        logger.info("Timetable exported to: %s", filepath)

        return filepath

    # =================================================================
    #  MASTER SHEET – all batches in one grid
    # =================================================================

    def _write_master_sheet(self, wb: Workbook):
        """Write the combined master timetable sheet."""
        ws = wb.create_sheet("Master Timetable")

        # Title row
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        title_cell = ws.cell(row=1, column=1, value="Lecture Time Table")
        title_cell.font = TITLE_FONT
        title_cell.alignment = CENTER_ALIGN

        # Generation timestamp
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=6)
        ts_cell = ws.cell(
            row=2, column=1,
            value=f"Generated on {datetime.now().strftime('%d %B %Y, %H:%M')}",
        )
        ts_cell.font = Font(name="Calibri", size=9, italic=True, color="666666")
        ts_cell.alignment = CENTER_ALIGN

        # Start the grid at row 4
        start_row = 4

        # Write a grid for each batch
        current_row = start_row
        for batch_label in sorted(self.by_batch.keys()):
            batch_rows = self.by_batch[batch_label]
            current_row = self._write_grid(
                ws, current_row, batch_label, batch_rows,
            )
            current_row += 2  # gap between batches

        # Set column widths
        ws.column_dimensions["A"].width = 18
        for col_idx in range(2, 7):
            ws.column_dimensions[get_column_letter(col_idx)].width = 28

    # =================================================================
    #  PER-BATCH SHEETS
    # =================================================================

    def _write_batch_sheet(self, wb: Workbook, batch_label: str):
        """Write a timetable sheet for a single batch."""
        # Sanitise the sheet name (Excel has a 31-char limit)
        safe_name = batch_label[:31].replace("/", "-")
        ws = wb.create_sheet(safe_name)

        batch_rows = self.by_batch[batch_label]

        # Title
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=6)
        title_cell = ws.cell(row=1, column=1, value=f"Timetable – {batch_label}")
        title_cell.font = TITLE_FONT
        title_cell.alignment = CENTER_ALIGN

        # Write the grid starting at row 3
        self._write_grid(ws, 3, batch_label, batch_rows)

        # Set column widths
        ws.column_dimensions["A"].width = 18
        for col_idx in range(2, 7):
            ws.column_dimensions[get_column_letter(col_idx)].width = 28

    # =================================================================
    #  FACULTY WORKLOAD SHEET
    # =================================================================

    def _write_faculty_sheet(self, wb: Workbook):
        """Write a summary sheet showing faculty weekly workload."""
        ws = wb.create_sheet("Faculty Workload")

        # Title
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=5)
        title_cell = ws.cell(row=1, column=1, value="Faculty Weekly Workload Summary")
        title_cell.font = TITLE_FONT
        title_cell.alignment = CENTER_ALIGN

        # Headers
        headers = ["Faculty Code", "Courses Taught", "Batches", "Total Sessions", "Load"]
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=3, column=col, value=header)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = CENTER_ALIGN
            cell.border = BORDER

        # Aggregate faculty data
        faculty_data = defaultdict(lambda: {
            "courses": set(),
            "batches": set(),
            "sessions": 0,
        })

        for row in self.rows:
            fc = row.get("faculty_code")
            if not fc:
                continue
            faculty_data[fc]["courses"].add(row["course_code"])
            faculty_data[fc]["batches"].add(row["batch_label"])
            faculty_data[fc]["sessions"] += 1

        # Write rows
        current_row = 4
        for fc in sorted(faculty_data.keys()):
            info = faculty_data[fc]

            ws.cell(row=current_row, column=1, value=fc).font = CELL_FONT
            ws.cell(row=current_row, column=2,
                    value=", ".join(sorted(info["courses"]))).font = CELL_FONT
            ws.cell(row=current_row, column=3,
                    value=", ".join(sorted(info["batches"]))).font = CELL_FONT
            ws.cell(row=current_row, column=4,
                    value=info["sessions"]).font = CELL_FONT

            # Load indicator
            if info["sessions"] > 10:
                load_text = "Heavy"
            elif info["sessions"] > 6:
                load_text = "Medium"
            else:
                load_text = "Light"

            ws.cell(row=current_row, column=5, value=load_text).font = CELL_FONT

            # Apply borders
            for col in range(1, 6):
                ws.cell(row=current_row, column=col).border = BORDER
                ws.cell(row=current_row, column=col).alignment = CENTER_ALIGN

            current_row += 1

        # Set column widths
        ws.column_dimensions["A"].width = 15
        ws.column_dimensions["B"].width = 30
        ws.column_dimensions["C"].width = 35
        ws.column_dimensions["D"].width = 16
        ws.column_dimensions["E"].width = 12

    # =================================================================
    #  GRID WRITER – shared logic for the slot/day grid
    # =================================================================

    def _write_grid(self, ws, start_row: int, batch_label: str,
                    batch_rows: list[dict]) -> int:
        """
        Write a time-slot grid for a batch.

        Layout:
            Row 0: Batch label header
            Row 1: Day headers (Mon–Fri)
            Rows 2+: One row per time slot

        Args:
            ws: Worksheet to write to.
            start_row: Row number to start writing at.
            batch_label: Label for the header.
            batch_rows: Timetable rows for this batch.

        Returns:
            The next available row after the grid.
        """
        # Build a lookup: (day_of_week, start_time) -> row data
        cell_lookup = {}
        for row in batch_rows:
            key = (row["day_of_week"], str(row["start_time"]))
            cell_lookup[key] = row

        # Batch label header
        ws.merge_cells(
            start_row=start_row, start_column=1,
            end_row=start_row, end_column=6,
        )
        header_cell = ws.cell(row=start_row, column=1, value=batch_label)
        header_cell.font = SUBHEADER_FONT
        header_cell.fill = SUBHEADER_FILL
        header_cell.alignment = CENTER_ALIGN
        header_cell.border = BORDER

        # Day headers row
        day_row = start_row + 1
        time_header = ws.cell(row=day_row, column=1, value="Time Slot")
        time_header.font = HEADER_FONT
        time_header.fill = HEADER_FILL
        time_header.alignment = CENTER_ALIGN
        time_header.border = BORDER

        for col_idx, day in enumerate(WEEKDAYS, start=2):
            cell = ws.cell(row=day_row, column=col_idx, value=day)
            cell.font = HEADER_FONT
            cell.fill = HEADER_FILL
            cell.alignment = CENTER_ALIGN
            cell.border = BORDER

        # Data rows – one per time slot
        current_row = day_row + 1
        for slot_time in self.time_slots:
            # Time label in column A
            time_cell = ws.cell(row=current_row, column=1, value=slot_time)
            time_cell.font = Font(name="Calibri", size=10, bold=True)
            time_cell.alignment = CENTER_ALIGN
            time_cell.border = BORDER

            # Day columns
            for col_idx, day in enumerate(WEEKDAYS, start=2):
                key = (day, slot_time)
                cell = ws.cell(row=current_row, column=col_idx)
                cell.border = BORDER
                cell.alignment = CENTER_ALIGN

                if key in cell_lookup:
                    entry = cell_lookup[key]
                    cell_text = self._format_cell(entry)
                    cell.value = cell_text
                    cell.font = CELL_FONT
                else:
                    cell.value = ""
                    cell.fill = FREE_FILL

            current_row += 1

        return current_row

    # =================================================================
    #  HELPERS
    # =================================================================

    def _extract_time_slots(self) -> list[str]:
        """
        Extract all unique time slot labels from the timetable data,
        sorted chronologically.

        Returns a list like: ["08:00", "09:00", "10:00", ...]
        """
        times = set()
        for row in self.rows:
            start = str(row["start_time"])
            # Normalise to HH:MM format
            if len(start) > 5:
                start = start[:5]
            times.add(start)

        return sorted(times)

    def _format_cell(self, entry: dict) -> str:
        """
        Format a timetable entry as a cell string.

        Format:
            Course Code
            Faculty Code
            Room Name

        Example:
            IT205
            PD
            LT-1
        """
        parts = [
            entry.get("course_code", ""),
            entry.get("faculty_code", ""),
            entry.get("classroom_name", ""),
        ]
        return "\n".join(parts)
