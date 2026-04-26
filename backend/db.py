"""
Database connection module.

Sets up SQLAlchemy engine, session factory, and the
declarative Base class that all ORM models inherit from.

Supports both PostgreSQL and SQLite:
    - PostgreSQL: set DATABASE_URL=postgresql://... in .env
    - SQLite:     set DATABASE_URL=sqlite:///timetable.db in .env

For PostgreSQL, uses the psycopg (v3) driver automatically.
"""

from sqlalchemy import create_engine, event, inspect, text
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
    _ensure_runtime_schema()


def _ensure_runtime_schema():
    """
    Apply tiny additive schema fixes for existing development databases.

    ``create_all`` creates missing tables but does not alter tables that
    already exist. The frontend now reloads the latest generated timetable
    from the database, so older DBs need the nullable generated_at column.
    """
    from backend.utils.helpers import build_slot_id

    recreate_slot_tables = False
    inspector = inspect(engine)

    if inspector.has_table("slot"):
        slot_columns = {column["name"] for column in inspector.get_columns("slot")}
        timetable_exists = inspector.has_table("timetable")
        timetable_columns = (
            {column["name"] for column in inspector.get_columns("timetable")}
            if timetable_exists else set()
        )

        with engine.begin() as connection:
            slot_count = connection.execute(text("SELECT COUNT(*) FROM slot")).scalar() or 0
            timetable_count = (
                connection.execute(text("SELECT COUNT(*) FROM timetable")).scalar() or 0
                if timetable_exists else 0
            )

            if "slot_id" not in slot_columns:
                if slot_count == 0 and timetable_count == 0:
                    if timetable_exists:
                        connection.execute(text("DROP TABLE IF EXISTS timetable"))
                    connection.execute(text("DROP TABLE IF EXISTS slot"))
                    recreate_slot_tables = True
                else:
                    connection.execute(text("ALTER TABLE slot ADD COLUMN slot_id VARCHAR(10)"))
                    rows = connection.execute(
                        text("SELECT ctid, day_of_week, start_time FROM slot")
                    ).fetchall()
                    for row in rows:
                        slot_id = build_slot_id(row.day_of_week, row.start_time)
                        connection.execute(
                            text("UPDATE slot SET slot_id = :slot_id WHERE ctid = :ctid"),
                            {"slot_id": slot_id, "ctid": row.ctid},
                        )
                    connection.execute(text("ALTER TABLE slot ALTER COLUMN slot_id SET NOT NULL"))
                    connection.execute(text("ALTER TABLE slot ADD PRIMARY KEY (slot_id)"))

            if timetable_exists and "slot_id" not in timetable_columns:
                if timetable_count == 0:
                    connection.execute(text("DROP TABLE IF EXISTS timetable"))
                    recreate_slot_tables = True
                else:
                    connection.execute(text("ALTER TABLE timetable ADD COLUMN slot_id VARCHAR(10)"))
                    rows = connection.execute(
                        text("SELECT auto_id, day_of_week, start_time FROM timetable")
                    ).fetchall()
                    for row in rows:
                        slot_id = build_slot_id(row.day_of_week, row.start_time)
                        connection.execute(
                            text("UPDATE timetable SET slot_id = :slot_id WHERE auto_id = :auto_id"),
                            {"slot_id": slot_id, "auto_id": row.auto_id},
                        )

    if recreate_slot_tables:
        Base.metadata.create_all(bind=engine)
        inspector = inspect(engine)

    if inspector.has_table("timetable"):
        columns = {column["name"] for column in inspector.get_columns("timetable")}
        if "generated_at" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE timetable ADD COLUMN generated_at TIMESTAMP"))

    if inspector.has_table("course"):
        credit_column = next(
            (
                column for column in inspector.get_columns("course")
                if column["name"] == "credits"
            ),
            None,
        )
        if credit_column is not None:
            type_name = credit_column["type"].__class__.__name__.lower()
            if "integer" in type_name:
                with engine.begin() as connection:
                    connection.execute(
                        text(
                            "ALTER TABLE course ALTER COLUMN credits "
                            "TYPE DOUBLE PRECISION USING credits::double precision"
                        )
                    )
