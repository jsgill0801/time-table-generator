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

    # PostgreSQL is the mandatory database. Specify DATABASE_URL in .env.
    DATABASE_URL = os.getenv("DATABASE_URL", "")

    # Flask-Session settings
    SESSION_TYPE = "filesystem"
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"

    # Allowed CORS Origins (comma-separated string)
    ALLOWED_ORIGINS = [
        o.strip()
        for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5000,http://127.0.0.1:5000").split(",")
        if o.strip()
    ]

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
