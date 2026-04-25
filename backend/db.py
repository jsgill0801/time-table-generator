"""
Database connection module.

Sets up SQLAlchemy engine, session factory, and the
declarative Base class that all ORM models inherit from.

Supports both PostgreSQL and SQLite:
    - PostgreSQL: set DATABASE_URL=postgresql://... in .env
    - SQLite:     set DATABASE_URL=sqlite:///timetable.db in .env

For PostgreSQL, uses the psycopg (v3) driver automatically.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import Config


# -----------------------------------------------------------------
# Declarative base – every ORM model inherits from this
# -----------------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------------
# Engine & session factory
# -----------------------------------------------------------------
_db_url = Config.DATABASE_URL

# Auto-switch to psycopg (v3) driver for PostgreSQL.
# psycopg2 does not support Python 3.14, so we use psycopg (v3).
# "postgresql://" defaults to psycopg2; "postgresql+psycopg://" uses v3.
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+psycopg://", 1)

_is_sqlite = _db_url.startswith("sqlite")

# SQLite does not support pool_pre_ping the same way
engine_kwargs = {
    "echo": Config.DEBUG if hasattr(Config, "DEBUG") else False,
}

if not _is_sqlite:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(_db_url, **engine_kwargs)

# SQLite needs WAL mode and foreign keys enabled
if _is_sqlite:
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# -----------------------------------------------------------------
# Session helper
# -----------------------------------------------------------------
def get_db():
    """
    Provide a transactional database session.

    Usage in Flask routes:
        db = next(get_db())
        ...
        db.close()

    Or with a context helper:
        with get_db_session() as db:
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -----------------------------------------------------------------
# Table creation
# -----------------------------------------------------------------
def init_db():
    """
    Create all tables that are registered with Base.metadata.

    Must be called AFTER all model modules have been imported,
    so that Base knows about every table.
    """
    # This import ensures all models are loaded before create_all
    import backend.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
