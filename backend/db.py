"""
Database connection module.

Sets up SQLAlchemy engine, session factory, and the
declarative Base class that all ORM models inherit from.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import Config


# -----------------------------------------------------------------
# Declarative base – every ORM model inherits from this
# -----------------------------------------------------------------
Base = declarative_base()


# -----------------------------------------------------------------
# Engine & session factory
# -----------------------------------------------------------------
engine = create_engine(
    Config.DATABASE_URL,
    echo=Config.DEBUG if hasattr(Config, "DEBUG") else False,
    pool_pre_ping=True,  # verify connections before use
)

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
