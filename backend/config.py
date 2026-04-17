"""
Configuration module.

Loads environment variables from .env and exposes
configuration classes for different environments.
"""

import os
from dotenv import load_dotenv

# Load .env file into environment variables
load_dotenv()


class Config:
    """Base configuration shared across all environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-fallback-secret-key")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/timetable_db"
    )

    # Flask-Session settings
    SESSION_TYPE = "filesystem"


class DevelopmentConfig(Config):
    """Development-specific settings."""

    DEBUG = True
    SQLALCHEMY_ECHO = True  # log SQL queries to console


class ProductionConfig(Config):
    """Production-specific settings."""

    DEBUG = False
    SQLALCHEMY_ECHO = False


class TestingConfig(Config):
    """Testing-specific settings."""

    TESTING = True
    DATABASE_URL = "sqlite:///test.db"
    SQLALCHEMY_ECHO = False
