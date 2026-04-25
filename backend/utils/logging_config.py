"""
Logging configuration for the backend.

Sets up structured logging with both console and file handlers.
All backend modules should use:

    import logging
    logger = logging.getLogger(__name__)
"""

import os
import logging
from logging.handlers import RotatingFileHandler


LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs",
)

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(app=None, level=logging.INFO):
    """
    Configure logging for the entire application.

    Sets up:
        1. Console handler (always enabled)
        2. Rotating file handler (logs/app.log, max 5 MB, 3 backups)

    Args:
        app:   Optional Flask app to attach the logger to.
        level: Logging level (default: INFO).
    """
    # Create log directory if it doesn't exist
    os.makedirs(LOG_DIR, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Avoid adding duplicate handlers on reload
    if root_logger.handlers:
        return

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File handler (rotating)
    file_path = os.path.join(LOG_DIR, "app.log")
    file_handler = RotatingFileHandler(
        file_path,
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    root_logger.addHandler(file_handler)

    # Quieten noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    if app:
        app.logger.info("Logging initialised.")
