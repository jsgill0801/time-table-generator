# University Timetable Generator

A full-stack web application for automated university timetable generation, built with **Flask** (Python) and vanilla **HTML/CSS/JS**. 

This repository is optimized for **Split Cloud Deployment** (hosting the static frontend on Vercel, the Python API on Render, and the database on Neon Serverless PostgreSQL).

## Features

- **Dashboard** — Live stats counter, recent runs overview, and one-click schedule generation.
- **Resource Management** — Strict CRUD interfaces for Courses, Faculty, Rooms, Batches, Categories, and Time Slots.
- **CSV Import** — Seamless bulk data upload via CSV files for every resource type.
- **Timetable Generation (Constraint-Based Scheduling Engine)**:
  - **Dynamic Day-Spreading Load Balancer**: Distributes academic load uniformly across all days of the week, ensuring active sessions are balanced globally.
  - **Intra-Day Randomization**: Shuffles session allocation across the day's slots to prevent congestion, maintaining empty slots dynamically while preventing course/faculty clashes.
  - **Hard Constraints Enforcement**: Prevents double-bookings for rooms, batches, and faculty members, ensures consecutive lecture slot safety, and respects room capacity constraints.
- **Cascading Deletions** — Deep database cascade cleanup across all mapped entities to guarantee zero orphan database constraints.
- **Strict Input Validation** — Robust front-end regex validations guarding against malformed database entries.
- **Timezone Integration** — Generates local execution records rendered explicitly using the browser's local timezone (IST).
- **Excel Export** — Download generated timetables as multi-sheet `.xlsx` workbooks matching official formats (overall, faculty-wise, room-wise, batch-wise).
- **Authentication & Authorization** — Secure session-based login/signup authenticated via hash signing with admin privilege guardrails.
- **User Management** — Only the master admin (`admin`) can manage other user accounts under the dedicated **Users** tab.
- **Modern UI/UX Polish**:
  - **Skeleton Shimmer Loaders**: Displays shimmering placeholders in tables and stat cards during database operations to avoid empty layout shifts.
  - **Mobile Responsive Drawer**: Uses a collapsible sliding menu drawer with a blurred backdrop overlay to fit phone and tablet viewports natively.

---

## Architecture & Tech Stack

| Layer      | Production Hosting | Technology |
|------------|--------------------|------------|
| **Frontend** | **Vercel** (Static Host) | HTML5, CSS3, Vanilla Javascript |
| **Backend**  | **Render** (Web Service) | Python 3.10+, Flask, SQLAlchemy, Gunicorn |
| **Database** | **Neon** (Serverless DB)  | PostgreSQL |
| **Export**   | (Backend Service) | openpyxl (Excel Workbook generation) |

---

## Deployment & Configuration

### 1. Database (Neon)
1. Create a free PostgreSQL instance on **[Neon](https://neon.tech/)**.
2. Copy the database connection string (`postgresql://...`).

### 2. Backend (Render)
1. Create a new **Web Service** on **[Render](https://render.com/)** connected to your repository.
2. Set the following settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT wsgi:app`
3. Add the following **Environment Variables**:
   - `DATABASE_URL`: *(Your Neon Connection String)*
   - `ALLOWED_ORIGINS`: `https://your-vercel-app-url.vercel.app` (to authorize CORS requests)
   - `FLASK_ENV`: `production`

### 3. Frontend (Vercel)
1. Open **[frontend/static/config.js](frontend/static/config.js)** and set your Render URL:
   ```javascript
   window.API_BASE_URL = "https://your-render-backend-url.onrender.com/api/v1";
   ```
2. Deploy the root of the project to **[Vercel](https://vercel.com/)**.
3. Vercel will automatically read the `vercel.json` config file to serve clean URLs (mapping `/dashboard` to `/frontend/dashboard.html` automatically).

---

## Local Development Quick Start

### Prerequisites
- Python 3.10+
- Local PostgreSQL instance or active Neon connection string

### Setup
1. Clone the repository and navigate to it:
   ```bash
   git clone https://github.com/jsgill0801/time-table-generator.git
   cd time-table-generator
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root folder with:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/dbname
   ```
4. Run the Flask backend locally:
   ```bash
   python -m backend.app
   ```
5. View the app at **http://localhost:5000**.

*Note: For local hosting, keep `window.API_BASE_URL` commented out or set to `"/api/v1"` in `frontend/static/config.js` to route requests to the local Flask server.*

---

## First-Time Setup & Credentials

1. **Register the Master Admin**: When the database is newly seeded/empty, navigate to `/signup` and create the very first account with:
   - **Username**: `admin`
   - **Password**: `admin123`
   - **Master Admin Password**: `admin123`
   *(The first database user must be named `admin` to establish master privilege control).*
2. **Log In**: Use `admin` and `admin123` on the login page.
3. **Import Demo Data**: Click **"Import Sample Data"** on the dashboard to populate the database with default configurations.
4. **Generate**: Click **"Run"** on the Dashboard, view the schedule under **"Timetable"**, and download Excel exports.

---

## API Endpoints

All API endpoints are prefixed with `/api/v1/`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Log in and start session |
| POST | `/auth/logout` | End current session |
| GET | `/courses/` | List all courses |
| POST | `/courses/` | Create a course |
| GET | `/batches/` | List all batches |
| GET | `/faculties/` | List all faculty |
| GET | `/classrooms/` | List all classrooms |
| GET | `/slots/` | List all time slots |
| GET | `/categories/` | List all categories |
| POST | `/import/courses` | Import courses from CSV |
| POST | `/import/batches` | Import batches from CSV |
| POST | `/import/faculties` | Import faculty from CSV |
| POST | `/import/classrooms`| Import classrooms from CSV |
| POST | `/import/slots` | Import slots from CSV |
| POST | `/import/categories`| Import categories from CSV |
| POST | `/generate/` | Trigger timetable generation |
| GET | `/timetable/` | Fetch generated timetable slots |
| GET | `/export/download/overall` | Download overall timetable Excel |
