# 📅 Time Table Generator

An automated scheduling system for academic institutions that produces conflict-free weekly timetables satisfying hard constraints and optimising soft constraints.

---

## 📋 Project Overview

The Time Table Generator (TTG) accepts structured input — Courses, Faculties, Classrooms, Slots, Batches, and Categories — and automatically assigns each course to a *(day, time-slot, room)* triple. The system enforces all hard constraints (no faculty/room/batch double-booking, capacity limits, faculty availability) and then applies a hill-climbing optimiser to improve schedule quality against soft constraints.

### Output Views

| View | Description |
|------|-------------|
| **Weekly Timetable** | Full grid of all slots × days with every scheduled session |
| **Batch-wise Timetable** | One sheet per batch/section |
| **Faculty-wise Schedule** | One sheet per faculty (idle gaps highlighted) |
| **Room-wise Allocation** | One sheet per classroom |
| **Conflict Report** | List of unresolved clashes with reasons (if any) |

---

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+ / Flask |
| ORM | SQLAlchemy |
| Database | PostgreSQL 15+ |
| Frontend | HTML / CSS / JavaScript |
| Excel Output | openpyxl |
| Testing | pytest |

---

## 📁 Project Structure

```
time-table-generator/
├── backend/
│   ├── app.py                     # Flask app factory
│   ├── config.py                  # Configuration classes
│   ├── db.py                      # Database engine & session
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── course.py
│   │   ├── batch.py
│   │   ├── faculty.py
│   │   ├── classroom.py
│   │   ├── slot.py
│   │   ├── batch_course.py
│   │   ├── faculty_course.py
│   │   ├── faculty_unavailable.py
│   │   └── timetable.py
│   ├── routes/                    # REST API endpoints (Blueprints)
│   │   ├── course_routes.py
│   │   ├── batch_routes.py
│   │   ├── faculty_routes.py
│   │   ├── classroom_routes.py
│   │   ├── slot_routes.py
│   │   └── generate_routes.py
│   ├── services/                  # Business logic
│   │   ├── data_service.py        # Data fetching & preprocessing
│   │   ├── validation_service.py  # Pre-generation checks
│   │   ├── scheduler.py           # Hard-constraint CSP engine
│   │   ├── optimiser.py           # Soft-constraint optimizer
│   │   ├── excel_writer.py        # Excel output generation
│   │   └── conflict_reporter.py   # Conflict report generation
│   ├── parsers/                   # CSV import parsers
│   │   ├── base_parser.py
│   │   ├── course_parser.py
│   │   ├── faculty_parser.py
│   │   └── ...
│   └── utils/                     # Shared utilities & errors
├── frontend/
│   ├── index.html                 # Main entry point
│   ├── css/styles.css             # Global styles
│   └── js/                        # Application logic
│       ├── app.js                 # Router / page loader
│       ├── api.js                 # API fetch wrapper
│       ├── forms/                 # Form components
│       └── viewers/               # List / editor components
├── tests/                         # pytest test suite
│   ├── test_models.py
│   ├── test_data_service.py
│   ├── test_validation.py
│   ├── test_scheduler.py
│   └── fixtures/                  # Sample test data
├── docs/                          # Project documentation
│   ├── SRS.md
│   ├── SDD.md
│   ├── risk_sheet.md
│   └── test_plan.md
├── sample_data/                   # Sample CSV input files
├── output/                        # Generated files (gitignored)
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## 🗄️ Database Schema

The data model comprises the following core entities:

| Table | Primary Key | Description |
|-------|------------|-------------|
| `course` | `course_id` (SERIAL) | Courses with L-T-P-C credits |
| `batch` | `batch_id` (SERIAL) | Program/Branch/Semester/Section |
| `faculty` | `faculty_code` (VARCHAR) | Faculty with max teaching load |
| `classroom` | `classroom_name` (VARCHAR) | Rooms with seating capacity |
| `slot` | `slot_id` (VARCHAR) | Day + time range |
| `category` | `category_id` (SERIAL) | Course categories (Core, Elective, etc.) |
| `batch_course` | `auto_id` (SERIAL) | Batch ↔ Course mapping with enrollment |
| `faculty_course` | `auto_id` (SERIAL) | Faculty ↔ Course mapping |
| `faculty_unavailable_slot` | `auto_id` (SERIAL) | Faculty scheduling blackout slots |
| `timetable` | `auto_id` (SERIAL) | Generated schedule assignments |

---

## ⚙️ Constraints

### Hard Constraints (Must Satisfy)
- No faculty double-booking in the same time slot
- Faculty scheduled only within available slots and max weekly load
- No batch double-booking in the same time slot
- Each batch receives exactly the required lectures per course per week
- No room double-booking in the same time slot
- Room capacity ≥ students enrolled
- Classes only within working days and hours
- No two consecutive lectures for a faculty member

### Soft Constraints (Optimisation Goals)
- Same-category courses in the same slots
- Minimise faculty idle gaps (without consecutive lectures)
- Avoid first/last slots of the day
- Distribute course sessions evenly across the week
- Prefer consistent time slots for courses
- Minimise room changes per batch per day

---

## 🚀 Getting Started

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

# Configure database
cp .env.example .env
# Edit .env with your PostgreSQL credentials

# Run the application
python -m backend.app
```

### Running Tests

```bash
pytest tests/ -v
```

---

## 👥 Team

| # | Name | Role |
|---|------|------|
| 1 | **Devansh Kukadia** | Project Lead & Backend Developer – Sprint planning, core scheduling algorithm |
| 2 | **Sri Sadana Dharavath** | Backend Developer – Input parsing/validation, constraint checking |
| 3 | **Sanya Vaishnavi** | Frontend Developer – UI forms, CRUD, timetable visualization |
| 4 | **Rasha Parmar** | QA & Documentation – Testing, risk management, documentation |
| 5 | **Jaspreet Singh Gill** | Database & File Handling – DB management, Excel output, conflict reports |

---

## 📄 License

This project is developed as part of an academic course project.
