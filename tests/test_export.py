"""
Tests for the ExportService.

Verifies that the Excel workbook is generated correctly
with proper structure: master sheet, per-batch sheets,
and faculty workload summary.
"""

import os
import pytest

from backend.services.export_service import ExportService


# -----------------------------------------------------------------
#  Sample timetable data for testing
# -----------------------------------------------------------------

def _sample_timetable():
    """Return a minimal timetable dataset for export testing."""
    return [
        {
            "auto_id": 1,
            "batch_course_id": 1,
            "faculty_code": "PD",
            "classroom_name": "LT-1",
            "slot_id": "MON-0800",
            "day_of_week": "Monday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-1",
            "course_code": "IT205",
            "course_name": "Data Structures",
            "ltpc": "3-0-0-3",
            "category_name": "Core",
            "batch_label": "BTech Sem-4 (ICT) Sec-A",
        },
        {
            "auto_id": 2,
            "batch_course_id": 2,
            "faculty_code": "AV",
            "classroom_name": "CEP211",
            "slot_id": "TUE-0900",
            "day_of_week": "Tuesday",
            "start_time": "09:00",
            "end_time": "09:50",
            "slot_name": "Slot-7",
            "course_code": "MA206",
            "course_name": "Probability",
            "ltpc": "3-1-0-4",
            "category_name": "Core",
            "batch_label": "BTech Sem-4 (ICT) Sec-A",
        },
        {
            "auto_id": 3,
            "batch_course_id": 3,
            "faculty_code": "PD",
            "classroom_name": "LT-1",
            "slot_id": "MON-0800",
            "day_of_week": "Monday",
            "start_time": "08:00",
            "end_time": "08:50",
            "slot_name": "Slot-1",
            "course_code": "HM108",
            "course_name": "English Communication",
            "ltpc": "2-0-0-2",
            "category_name": "Humanities",
            "batch_label": "BTech Sem-4 (CS)",
        },
    ]


# =================================================================
#  Tests
# =================================================================

class TestExportService:
    """Tests for the Excel export service."""

    def test_generates_xlsx_file(self, tmp_path, monkeypatch):
        """The service should create an .xlsx file on disk."""
        # Override the output directory to use a temp path
        monkeypatch.setattr(
            "backend.services.export_service.OUTPUT_DIR",
            str(tmp_path),
        )

        service = ExportService(_sample_timetable())
        filepath = service.generate()

        assert os.path.exists(filepath)
        assert filepath.endswith(".xlsx")
        assert os.path.getsize(filepath) > 0

    def test_workbook_has_correct_sheets(self, tmp_path, monkeypatch):
        """The workbook should have master + per-batch + faculty sheets."""
        monkeypatch.setattr(
            "backend.services.export_service.OUTPUT_DIR",
            str(tmp_path),
        )

        service = ExportService(_sample_timetable())
        filepath = service.generate()

        from openpyxl import load_workbook
        wb = load_workbook(filepath)

        sheet_names = wb.sheetnames

        # Should have: Master Timetable, 2 batch sheets, Faculty Workload
        assert "Master Timetable" in sheet_names
        assert "Faculty Workload" in sheet_names
        assert len(sheet_names) == 4  # master + 2 batches + faculty

    def test_master_sheet_has_title(self, tmp_path, monkeypatch):
        """The master sheet should contain a title."""
        monkeypatch.setattr(
            "backend.services.export_service.OUTPUT_DIR",
            str(tmp_path),
        )

        service = ExportService(_sample_timetable())
        filepath = service.generate()

        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb["Master Timetable"]

        assert ws.cell(row=1, column=1).value == "Lecture Time Table"

    def test_faculty_sheet_has_data(self, tmp_path, monkeypatch):
        """The faculty sheet should list faculty and their load."""
        monkeypatch.setattr(
            "backend.services.export_service.OUTPUT_DIR",
            str(tmp_path),
        )

        service = ExportService(_sample_timetable())
        filepath = service.generate()

        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb["Faculty Workload"]

        # Header row should have "Faculty Code"
        assert ws.cell(row=3, column=1).value == "Faculty Code"

        # Data should have at least PD and AV
        faculty_codes = []
        for row in range(4, ws.max_row + 1):
            val = ws.cell(row=row, column=1).value
            if val:
                faculty_codes.append(val)

        assert "PD" in faculty_codes
        assert "AV" in faculty_codes

    def test_empty_timetable(self, tmp_path, monkeypatch):
        """An empty timetable should still produce a valid file."""
        monkeypatch.setattr(
            "backend.services.export_service.OUTPUT_DIR",
            str(tmp_path),
        )

        service = ExportService([])
        filepath = service.generate()

        assert os.path.exists(filepath)
        assert filepath.endswith(".xlsx")

    def test_cell_format(self):
        """Cell content should be formatted as code/faculty/room."""
        service = ExportService(_sample_timetable())
        entry = _sample_timetable()[0]
        result = service._format_cell(entry)

        assert "IT205" in result
        assert "PD" in result
        assert "LT-1" in result
