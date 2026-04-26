"""
Application bootstrap helpers.

Ensures the local project starts with one admin account and a runnable
demo dataset when the configured database does not yet have working
input data.
"""

from werkzeug.security import generate_password_hash

from backend.config import Config
from backend.db import get_db
from backend.models.user import User
from backend.models.course import Course
from backend.models.batch import Batch
from backend.models.faculty import Faculty
from backend.models.classroom import Classroom
from backend.models.slot import Slot
from backend.models.category import Category
from backend.models.batch_course import BatchCourse
from backend.models.faculty_course import FacultyCourse
from backend.seed import seed_dataset
from backend.services.auth_service import create_user
from backend.utils.errors import AuthError, DataError


def ensure_default_admin_and_demo_data():
    """Create the default admin account and seed demo data when needed."""
    db = next(get_db())

    try:
        admin_user = (
            db.query(User)
            .filter(User.username == Config.DEFAULT_ADMIN_USERNAME)
            .first()
        )

        if admin_user:
            admin_user.password_hash = generate_password_hash(Config.DEFAULT_ADMIN_PASSWORD)
            admin_user.role = "admin"
            db.commit()
        else:
            create_user(
                db,
                username=Config.DEFAULT_ADMIN_USERNAME,
                email=Config.DEFAULT_ADMIN_EMAIL,
                password=Config.DEFAULT_ADMIN_PASSWORD,
                role="admin",
            )

        # IMPORTANT: Do not auto-seed demo data in serious deployments.
        # Demo seeding is available only via the explicit admin endpoint:
        # POST /api/v1/data/bootstrap-admin-demo

    except (AuthError, DataError):
        db.rollback()
        raise
    finally:
        db.close()
