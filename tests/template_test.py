"""Template tests and fixtures for contributors.

Contains example pytest fixtures and two starter tests:
- `test_course_parser` (unit test for CSV parser)
- `test_signup_and_login` (integration test using Flask test client)

Use this as a starting point for adding more tests.
"""
import pytest

from backend.app import create_app
from backend.config import TestingConfig
from backend.db import init_db


@pytest.fixture
def app():
    app = create_app(TestingConfig)
    # Ensure DB tables exist for integration tests
    init_db()

    yield app


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
