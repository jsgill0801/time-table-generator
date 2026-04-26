# University Timetable Generator

A full-stack web application for automated university timetable generation, built with **Flask** (Python) and vanilla **HTML/CSS/JS**.

## Features

- **Dashboard** — Overview of all configured resources with one-click timetable generation
- **Resource Management** — CRUD interfaces for Courses, Faculty, Rooms, Batches, Categories, and Time Slots
- **CSV Import** — Bulk data upload via CSV files for every resource type
- **Timetable Generation** — Server-side constraint-based scheduling engine with conflict detection
- **Excel Export** — Download generated timetables as multi-sheet `.xlsx` workbooks (overall, faculty-wise, room-wise, batch-wise)
- **Authentication** — Session-based login/signup system
- **Conflict Reporting** — Automatic detection and display of scheduling conflicts

## Tech Stack

| Layer      | Technology                         |
|------------|-------------------------------------|
| Backend    | Python 3.10+, Flask, SQLAlchemy     |
| Frontend   | HTML5, CSS3 (Inter + Georgia fonts), Vanilla JS |
| Database   | PostgreSQL (primary) / SQLite (fallback) |
| Export     | openpyxl (Excel generation)         |

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL (optional — SQLite works out of the box)

### Setup

```bash
# 1. Navigate to the project directory
cd time-table-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional — defaults work with SQLite)
#    Edit .env to set DATABASE_URL for PostgreSQL:
#    DATABASE_URL=postgresql://user:password@localhost:5432/TTG-main

# 4. Run the application
python -m backend.app
```

The application starts at **http://localhost:5000**

### First-Time Setup

1. Open http://localhost:5000 → you'll see the **Login** page
2. Click **"Create one"** to register an admin account
3. Log in with your credentials
4. Use the sidebar to navigate between pages
5. Import data via CSV or add entries manually using the **Add** button
6. Click **Run** on the Dashboard to generate the timetable
7. Go to **Timetable** page to download the Excel export

## Project Structure

```
time-table-generator/
├── backend/
│   ├── app.py                  # Flask application factory
│   ├── config.py               # Environment configuration
│   ├── db.py                   # SQLAlchemy engine & session
│   ├── models/                 # Database models (ORM)
│   ├── routes/                 # API endpoints + frontend serving
│   │   ├── frontend_routes.py  # Serves HTML pages
│   │   ├── import_routes.py    # CSV import endpoints
│   │   ├── generate_routes.py  # Timetable generation
│   │   ├── export_routes.py    # Excel download
│   │   └── ...                 # CRUD routes for each entity
│   ├── services/               # Business logic layer
│   │   ├── scheduler.py        # Hard-constraint scheduler
│   │   ├── optimiser.py        # Soft-constraint optimizer
│   │   ├── export_service.py   # Excel workbook generation
│   │   └── ...
│   ├── parsers/                # CSV parsing & validation
│   └── utils/                  # Helpers, middleware, logging
├── frontend/
│   ├── templates/              # HTML pages
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── courses.html
│   │   └── ...
│   └── static/                 # CSS & JavaScript
│       ├── style.css           # Full application stylesheet
│       ├── api.js              # Centralised API client
│       └── script.js           # Application logic & UI rendering
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
└── README.md
```

## API Endpoints

All API endpoints are prefixed with `/api/v1/`.

| Method | Endpoint                | Description                     |
|--------|-------------------------|---------------------------------|
| POST   | `/auth/signup`          | Register a new user             |
| POST   | `/auth/login`           | Log in and start session        |
| POST   | `/auth/logout`          | End current session             |
| GET    | `/courses/`             | List all courses                |
| POST   | `/courses/`             | Create a course                 |
| GET    | `/batches/`             | List all batches                |
| GET    | `/faculties/`           | List all faculty                |
| GET    | `/classrooms/`          | List all classrooms             |
| GET    | `/slots/`               | List all time slots             |
| GET    | `/categories/`          | List all categories             |
| POST   | `/import/courses`       | Import courses from CSV         |
| POST   | `/import/batches`       | Import batches from CSV         |
| POST   | `/import/faculties`     | Import faculty from CSV         |
| POST   | `/import/classrooms`    | Import classrooms from CSV      |
| POST   | `/import/slots`         | Import slots from CSV           |
| POST   | `/import/categories`    | Import categories from CSV      |
| POST   | `/generate/`            | Trigger timetable generation    |
| GET    | `/export/download`      | Download timetable as Excel     |
| GET    | `/export/preview`       | Preview timetable grid as JSON  |
| GET    | `/data/counts`          | Record counts per table         |

## CSV Import Formats

Each resource page shows the required CSV column headers. Examples:

**Courses:**
```csv
course_code,course_name,lectures,tutorials,labs,credits
ICT201,Data Structures,3,1,0,4
```

**Faculty:**
```csv
faculty_code,faculty_name,faculty_email,max_load
PD,Dr. Priya Desai,pd@college.edu,18
```

**Batches:**
```csv
program,branch,semester,section
BTech,Computer Science,4,A
```

## Environment Variables

| Variable       | Default                                | Description            |
|----------------|----------------------------------------|------------------------|
| `DATABASE_URL` | `sqlite:///timetable.db`               | Database connection    |
| `SECRET_KEY`   | *(auto-generated)*                     | Flask session signing  |
| `FLASK_ENV`    | `development`                          | Flask environment mode |

## License

This project is developed for academic purposes as part of the university curriculum.
