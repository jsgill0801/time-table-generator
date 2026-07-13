# Project Description & Testing Guide

This document summarizes the `time-table-generator` project and provides structured information for automated testing (unit tests, white-box, black-box, integration, and system tests).

---

## Project Summary

- Name: Time Table Generator
- Stack: Python 3.10+, Flask backend, SQLAlchemy ORM, vanilla HTML/CSS/JS frontend
- Purpose: Create and export university timetables from user-provided resources (courses, faculty, rooms, batches, slots) and an optimisation/scheduler engine.

Key directories:

- `backend/` — Flask application, routes, models, services, parsers, and utilities.
- `frontend/` — static assets and Jinja templates served by Flask.
- `sample_data/` — CSV files used by the seeder for sample records.
- `tests/` — pytest test suite.

Files of interest:

- `backend/app.py` — application factory and development server entry point.
- `backend/config.py` — `.env` loading and `DevelopmentConfig`/`TestingConfig` classes.
- `backend/db.py` — SQLAlchemy engine/session helpers (DB initialisation).
- `backend/seed.py` — seeder that reads `sample_data/` and inserts records.
- `backend/parsers/` — CSV parsing & validation logic (good unit-test targets).
- `backend/services/` — scheduler and optimiser modules (algorithmic core, white-box testing focus).
- `frontend/` — templates and `static/` assets for black-box (UI) tests.

---

## How to run (developer instructions)

Prerequisites:

- Python 3.10+ installed
- (Optional) PostgreSQL if `DATABASE_URL` points to it; otherwise SQLite default is used.

Quick start (from repository root):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
cd time-table-generator
pip install -r requirements.txt
# (optional) edit .env to configure DATABASE_URL
python -m backend.app
```

The app listens at `http://localhost:5000` by default.

Seeder (loads `sample_data/` into DB):

```powershell
python -m backend.seed
```

Run tests:

```powershell
pytest -q
```

Notes:

- Configuration is read from `time-table-generator/.env` using `python-dotenv`.
- `backend/config.py` defines `TestingConfig` which uses an SQLite `test.db`.

---

## API & UI surface (for black-box testing)

All API endpoints are prefixed by `/api/v1/` (see README). Important endpoints:

- `POST /auth/signup` — register user
- `POST /auth/login` — login
- `POST /auth/logout` — logout
- `GET /courses/` — list courses
- `POST /courses/` — create course
- `GET /batches/`, `GET /faculties/`, `GET /classrooms/`, `GET /slots/`, `GET /categories/`
- `POST /import/<resource>` — CSV import endpoints (courses, batches, faculties, classrooms, slots, categories)
- `POST /generate/` — trigger timetable generation
- `GET /export/download` — download Excel workbook

Frontend pages are served by the `frontend_routes` blueprint and include login, dashboard, resource CRUD pages, generate page, and export/preview functionality. Use UI flows to exercise the end-to-end system.

---

## Testing targets and recommendations

1) Unit tests (fast, isolated)

- Parsers in `backend/parsers/`: validate correct parsing and error handling for malformed CSV rows. Provide many test vectors including missing fields, extra fields, invalid datatypes, and BOM-prefixed files.
- Models & small helpers in `backend/utils/` and `backend/models/*`: creation, validation, and helper functions.
- `backend/services/optimiser.py` and `backend/services/scheduler.py`: design white-box tests for known small inputs and assert deterministic outputs (or properties such as no overlapping assignments, respecting `max_load`, preserving slot constraints).

Mocks/stubs:

- Mock the DB session (or use an in-memory SQLite) to keep unit tests fast — `TestingConfig` sets a test DB.
- For file reads (CSV), use `io.StringIO` with small sample data instead of disk files.

2) Integration tests

- Use the Flask test client (`app.test_client()`) to call endpoints defined in `backend/routes/`. Validate JSON responses, status codes, and DB side-effects.
- Tests should cover import endpoints (`/import/*`), authentication flows, and `POST /generate/` to verify generation runs without raising exceptions and that exported data exists.

3) Black-box / End-to-end tests

- Use a real browser automation tool (Selenium / Playwright) to exercise the UI: sign up, login, import CSVs via the frontend, run generation, and download the Excel export.
- Validate the downloaded `.xlsx` (openpyxl) or the export preview JSON from `/export/preview`.

4) White-box tests

- Focus on `scheduler.py` and `optimiser.py` internals: test constraint enforcement functions, heuristics, and scoring functions.
- Use parametrised tests with small synthetic datasets to check corner-case behaviour.

5) Security & error handling tests

- Test session handling (login/logout), missing/invalid tokens (if any), and CSRF/authorization boundaries for protected endpoints.
- Test import endpoints with malicious or malformed CSV input and assert graceful validation errors (400 responses) rather than 500 crashes.

---

## Sample test cases (suggested)

- Parsers:
  - Valid `courses.csv` yields N parsed rows with expected fields.
  - Missing `course_code` returns a `DataError` or parser-specific validation error.

- Scheduler/Optimiser:
  - Small synthetic input: 2 courses, 1 faculty, 2 slots, 1 classroom — run scheduler and assert:
    - No faculty exceeds `max_load`.
    - No slot has more than one assignment per classroom.
    - Each required lecture count is scheduled.

- Routes:
  - `POST /auth/signup` then `POST /auth/login` returns 200 and sets session cookie.
  - `POST /import/courses` with CSV attaches courses to the requesting user.

---

## Test data and fixtures

- Use the `sample_data/` CSV files as canonical fixtures: `sample_data/*.csv`.
- For unit tests that need an empty DB, use `TestingConfig` or use an in-memory SQLite by overriding `DATABASE_URL` to `sqlite:///:memory:` in the test setup.

Pytest fixtures to add (recommended):

- `app` — builds `create_app(TestingConfig)` and yields Flask app for tests.
- `db` — initialised fresh per test or per-module; tear down by dropping tables.
- `client` — Flask test client using `app.test_client()`.

---

## Common failure modes & checks for test harness

- Environment variable loading: `.env` must be in the project root; `backend/config.py` loads it using `python-dotenv`.
- File encodings: CSV files may have BOM; parsers should handle `utf-8-sig`.
- Time fields for slots are parsed into Python `datetime.time` — tests should pass strings like `08:30` and `17:00`.

---

## Commands summary (copy-paste)

```powershell
# Setup venv and install deps
python -m venv .venv
.venv\Scripts\Activate.ps1
cd time-table-generator
pip install -r requirements.txt

# Seed sample data
python -m backend.seed

# Run server
python -m backend.app

# Run tests
pytest -q
```

---

## Deliverables for automated testers (Claude or other)

Provide this file and the repository root. Recommended testing inputs:

- `sample_data/*.csv` (included)
- `.env` (use default values; no live DB necessary)
- Use `TestingConfig` or set `DATABASE_URL=sqlite:///test.db` for repeatable runs.

If you want, I can also generate a small `tests/template_test.py` with example pytest fixtures and a few starter tests (parsers + an integration test that runs the Flask test client). Ask and I'll add it.

---

End of file.
