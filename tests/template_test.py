"""Template tests and fixtures for contributors.

Contains example pytest fixtures and two starter tests:
- `test_course_parser` (unit test for CSV parser)
- `test_signup_and_login` (integration test using Flask test client)

Use this as a starting point for adding more tests.
"""
import os
import pytest

# Override DATABASE_URL before importing backend app
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.app import create_app
from backend.config import TestingConfig
from backend.db import init_db


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    # Ensure DB tables exist for integration tests
    init_db()

    yield app

    from backend.db import Base, engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(app):
    return app.test_client()


def test_course_parser():
    from backend.parsers.course_parser import CourseParser

    csv = """course_code,course_name,lectures,tutorials,labs,credits
IT201,Algorithms,3,0,0,3
"""
    parser = CourseParser()
    rows = parser.parse(csv)

    assert len(rows) == 1
    assert rows[0]["course_code"] == "IT201"


def test_signup_and_login(client):
    # Signup (first user becomes admin)
    resp = client.post(
        "/api/v1/auth/signup",
        json={"username": "ci_user", "email": "ci@local", "password": "secretpw"},
    )
    assert resp.status_code == 201

    # Login with same credentials
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "ci_user", "password": "secretpw"},
    )
    assert resp.status_code == 200
    data = resp.get_json()
    assert data.get("user") and data["user"].get("username") == "ci_user"


def test_clear_timetable_on_mutation(client):
    # 1. Signup admin
    resp = client.post(
        "/api/v1/auth/signup",
        json={"username": "admin", "email": "admin@local", "password": "adminpassword"},
    )
    assert resp.status_code == 201

    # 2. Login admin to establish session
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "adminpassword"},
    )
    assert resp.status_code == 200

    # 3. Create a timetable record manually in DB
    from backend.db import get_db
    from backend.models.timetable import Timetable
    from datetime import time
    db = next(get_db())
    
    # We must insert dependent course, batch, faculty, classroom, slot first
    from backend.models.course import Course
    from backend.models.batch import Batch
    from backend.models.faculty import Faculty
    from backend.models.classroom import Classroom
    from backend.models.slot import Slot
    from backend.models.batch_course import BatchCourse
    
    c = Course(course_code="CS101", course_name="Intro", lectures=3, tutorials=0, labs=0, credits=3)
    b = Batch(program="BTech", branch="CS", semester=1, section="A")
    f = Faculty(faculty_code="INS", faculty_name="Instructor", max_load=12, faculty_email="ins@local")
    cr = Classroom(classroom_name="R1", capacity=60)
    sl = Slot(slot_id="S1", day_of_week="Monday", start_time=time(9, 0), end_time=time(9, 50), slot_name="Slot-1")
    
    db.add_all([c, b, f, cr, sl])
    db.commit()
    
    bc = BatchCourse(batch_id=b.batch_id, course_id=c.course_id, category_id=None, students_enrolled=50)
    db.add(bc)
    db.commit()
    
    t = Timetable(
        batch_course_id=bc.auto_id,
        faculty_code=f.faculty_code,
        classroom_name=cr.classroom_name,
        slot_id=sl.slot_id,
        day_of_week="Monday",
        start_time=time(9, 0),
        end_time=time(9, 50),
        slot_name="Slot-1",
        course_code="CS101",
        course_name="Intro",
        ltpc="3-0-0-3",
        batch_label="BTech CS Sem 1 A",
    )
    db.add(t)
    db.commit()
    
    # Assert timetable row exists
    assert db.query(Timetable).count() == 1
    db.close()

    # 4. Perform a mutating request (e.g. create a new course via API)
    resp = client.post(
        "/api/v1/courses/",
        json={
            "course_code": "CS102",
            "course_name": "Data Struct",
            "lectures": 3,
            "tutorials": 0,
            "labs": 0,
            "credits": 3
        }
    )
    assert resp.status_code == 201

    # 5. Assert the timetable table is now completely empty
    db = next(get_db())
    assert db.query(Timetable).count() == 0
    db.close()
