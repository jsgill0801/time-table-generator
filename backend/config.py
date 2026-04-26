"""
Configuration module.

Loads environment variables from .env and exposes
configuration classes for different environments.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Resolve the .env path relative to THIS file's parent (project root)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=False)


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key")

    # Default to SQLite for zero-setup development.
    # Switch to PostgreSQL by editing .env.
    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "sqlite:///timetable.db",
    )

    # Flask-Session settings
    SESSION_TYPE = "filesystem"

    DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
    DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@ttg.local")
    DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")


class DevelopmentConfig(Config):
    """Development-specific settings."""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production-specific settings."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing-specific settings."""

    TESTING = True
    DATABASE_URL = "sqlite:///test.db"
    SQLALCHEMY_ECHO = False
