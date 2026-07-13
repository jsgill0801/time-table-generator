# University Timetable Generator

A full-stack web application for automated university timetable generation, built with **Flask** (Python) and vanilla **HTML/CSS/JS**.

## Features

- **Dashboard** — Live stats counter and overview of all configured resources with one-click generation.
- **Resource Management** — Strict CRUD interfaces for Courses, Faculty, Rooms, Batches, Categories, and Time Slots.
- **CSV Import** — Seamless bulk data upload via CSV files for every resource type.
- **Timetable Generation (Constraint-Based Scheduling Engine)**:
  - **Dynamic Day-Spreading Load Balancer**: Distributes academic load uniformly across all days of the week, ensuring active sessions are balanced globally and no days (like Thursday or Friday) are left empty.
  - **Intra-Day Randomization**: Randomly shuffles session allocation across the day's slots to prevent congestion, maintaining empty slots dynamically while preventing course/faculty clashes.
  - **Hard Constraints Enforcement**: Prevents double-bookings for rooms, batches, and faculty members, ensures consecutive lecture slot safety, and respects room capacity constraints.
- **Cascading Deletions** — Deep database cascade cleanup across all mapped entities (Courses, Batches, Categories, Classrooms, Slots, and Faculty) to guarantee zero orphan database constraints.
- **Strict Input Validation** — Robust front-end regex validations guarding against malformed database entries (alphabets-only for names, valid formatting for emails, positive numbers, and strict codes).
- **Timezone Integration** — Generates local execution records rendered explicitly using the browser's local timezone (IST).
- **Excel Export** — Download generated timetables as multi-sheet `.xlsx` workbooks matching official formats (overall, faculty-wise, room-wise, batch-wise) generated via `openpyxl`.
- **Authentication & Authorization** — Secure session-based login/signup authenticated via hash signing with admin privilege guardrails.
- **Conflict Reporting** — Automatic diagnosis and reporting of scheduling bottlenecks and conflicts.

## Tech Stack

| Layer      | Technology                         |
|------------|-------------------------------------|
| Backend    | Python 3.10+, Flask, SQLAlchemy     |
| Frontend   | HTML5, CSS3 (Inter + Georgia fonts), Vanilla JS |
| Database   | PostgreSQL (Mandatory)              |
| Export     | openpyxl (Excel generation)         |

## Quick Start

### Prerequisites

- Python 3.10 or higher
- PostgreSQL Server

### Setup

```bash
# 1. Navigate to the project directory
cd time-table-generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
#    Edit .env to set your PostgreSQL connection string:
#    DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# 4. Run the application
python -m backend.app
```

The application starts at **http://localhost:5000**

### First-Time Setup & Testing

1. **Start the Application**: Run `python -m backend.app` and open http://localhost:5000 in your browser.
2. **Log In as Master Admin**: Log in directly with the default master admin credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. **Registering New Accounts**: To create a new user or administrator:
   - Click **"Create one"** on the login page (or go to `/signup`).
   - Fill in the username, email, and password.
   - Enter the **Master Admin Password** (`admin123`) to authorize the account creation. All newly registered accounts are set up as administrators.
4. **User Management**:
   - Only the master admin (`admin`) can view and manage user accounts.
   - When logged in as `admin`, click the **"Users"** tab in the sidebar to see all registered accounts and delete them if needed (except for the core `admin` account).
5. **Generate Timetable**: Use the sidebar to navigate, import sample data via CSV (under each resource page) or add manually, then click **Run** on the Dashboard and export on the **Timetable** page.

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
| `DATABASE_URL` | `postgresql://user:password@localhost:5432/dbname` | PostgreSQL database connection string (Mandatory) |
| `SECRET_KEY`   | *(auto-generated)*                     | Flask session signing  |
| `FLASK_ENV`    | `development`                          | Flask environment mode |

## License

This project is developed for academic purposes as part of the university curriculum.
