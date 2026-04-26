"""
Factory reset utility for local SQLite development.

Deletes the SQLite database files so you can start with a clean dataset:
  - timetable.db
  - timetable.db-wal
  - timetable.db-shm

This does NOT touch your source code. After running, start the server and
create a new admin account via the first signup.
"""

from __future__ import annotations

import os


def _delete(path: str) -> bool:
    try:
        os.remove(path)
        return True
    except FileNotFoundError:
        return False


def main() -> None:
    base = os.path.abspath("timetable.db")
    deleted = {
        "timetable.db": _delete(base),
        "timetable.db-wal": _delete(base + "-wal"),
        "timetable.db-shm": _delete(base + "-shm"),
    }
    print("Reset complete. Deleted:", {k: v for k, v in deleted.items()})


if __name__ == "__main__":
    main()

