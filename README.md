# Time Table Generator

An automated scheduling system for academic institutions that produces conflict-free weekly timetables satisfying hard constraints and optimising soft constraints.

---

## Project Overview

The Time Table Generator (TTG) accepts structured input — Courses, Faculties, Classrooms, Slots, Batches, and Categories — and automatically assigns each course to a (day, time-slot, room) triple. The system enforces all hard constraints (no faculty/room/batch double-booking, capacity limits, teaching load) and applies a hill-climbing optimiser to improve schedule quality against soft constraints.

The system includes user authentication (signup, login, logout) to restrict access to authorized administrators.

### Output Views

| View | Description |
|------|-------------|
| Weekly Timetable | Full grid of all time blocks × days showing every scheduled session |
| Batch-wise Timetable | One sheet per batch/section |
| Faculty-wise Schedule | One sheet per faculty member (idle gaps highlighted) |
| Room-wise Allocation | One sheet per classroom |
| Conflict Report | Persisted record of unresolved clashes with reasons |

The Excel output replicates the university's standard timetable format: a slot-based rotating grid with 6 fields per day (course code, course name, L-T-P-C, category, faculty code, room).

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / Flask |
| Authentication | Flask-Session + Werkzeug |
| ORM | SQLAlchemy |
| Database | PostgreSQL 15+ |
| Frontend | HTML / CSS / JavaScript |
| Excel Output | openpyxl |
| Testing | pytest |

---

## Project Structure

```
time-table-generator/
├── backend/
│   ├── app.py                     # Flask app factory
│   ├── config.py                  # Configuration
│   ├── db.py                      # Database engine & session
│   ├── models/
│   │   ├── user.py                # User authentication model
│   │   ├── course.py
│   │   ├── batch.py
│   │   ├── faculty.py             # Includes faculty_email
│   │   ├── classroom.py
│   │   ├── slot.py
│   │   ├── batch_course.py
│   │   ├── faculty_course.py
│   │   ├── timetable.py           # Full denormalized fields
│   │   └── conflict_report.py     # Persisted conflict records
│   ├── routes/
│   │   ├── auth_routes.py         # Signup, login, logout
│   │   ├── course_routes.py
│   │   ├── batch_routes.py
│   │   ├── faculty_routes.py
│   │   ├── classroom_routes.py
│   │   ├── slot_routes.py
│   │   └── generate_routes.py
│   ├── services/
│   │   ├── auth_service.py        # Password hashing, session management
│   │   ├── data_service.py        # Data fetching & preprocessing
│   │   ├── validation_service.py  # Pre-generation integrity checks
│   │   ├── scheduler.py           # Hard-constraint CSP engine
│   │   ├── optimiser.py           # Soft-constraint optimizer
│   │   ├── excel_writer.py        # University-format Excel generation
│   │   └── conflict_reporter.py   # Conflict report generation
│   ├── parsers/                   # CSV import parsers
│   └── utils/                     # Custom exceptions & helpers
├── frontend/
│   ├── index.html
│   ├── login.html
│   ├── signup.html
│   ├── css/styles.css
│   └── js/
│       ├── app.js
│       ├── api.js
│       ├── auth.js
│       ├── forms/
│       └── viewers/
├── tests/
├── docs/
├── sample_data/
├── output/                        # Generated files (gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Database Schema

| Table | Primary Key | Description |
|-------|------------|-------------|
| `app_user` | `user_id` (SERIAL) | User authentication (username, email, password hash, role) |
| `course` | `course_id` (SERIAL) | Courses with L-T-P-C credit notation |
| `batch` | `batch_id` (SERIAL) | Program / Branch / Semester / Section |
| `faculty` | `faculty_code` (VARCHAR) | Faculty with email and max teaching load |
| `classroom` | `classroom_name` (VARCHAR) | Rooms with seating capacity |
| `slot` | `slot_id` (VARCHAR) | Day + time range + slot name |
| `category` | `category_id` (SERIAL) | Course categories (Core, Elective, etc.) |
| `batch_course` | `auto_id` (SERIAL) | Batch-Course mapping with enrollment count |
| `faculty_course` | `auto_id` (SERIAL) | Faculty-Course mapping |
| `timetable` | `auto_id` (SERIAL) | Generated schedule with all denormalized output fields |
| `conflict_report` | `conflict_id` (SERIAL) | Persisted unresolved scheduling conflicts |

---

## Constraints

### Hard Constraints
- No faculty double-booking in the same time slot
- Faculty scheduled within max weekly teaching load
- No batch double-booking in the same time slot
- Each batch receives exactly the required lectures per course per week
- No room double-booking in the same time slot
- Room capacity >= students enrolled
- Classes only within working days and designated hours
- No two consecutive lectures for a faculty member

### Soft Constraints (Optimisation)
- Same-category courses in the same slots
- Minimise faculty idle gaps (without consecutive lectures)
- Avoid first/last slots of the day
- Distribute course sessions evenly across the week
- Prefer consistent time slots for courses
- Minimise room changes per batch per day

---

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/<your-org>/time-table-generator.git
cd time-table-generator

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your PostgreSQL credentials and SECRET_KEY

# Run the application
python -m backend.app
```

### Running Tests

```bash
pytest tests/ -v
```

---

## License

This project is developed as part of an academic course project.
