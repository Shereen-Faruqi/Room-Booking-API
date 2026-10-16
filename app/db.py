"""SQLite connection helper."""
import os
import sqlite3

DEFAULT_DB_PATH = "./bookings.db"


def db_path() -> str:
    """Database file location, taken from BOOKINGS_DB (default ./bookings.db)."""
    return os.environ.get("BOOKINGS_DB", DEFAULT_DB_PATH)


def connect(path: str | None = None) -> sqlite3.Connection:
    """Open a new connection. Rows can be read by column name."""
    conn = sqlite3.connect(path or db_path())
    conn.row_factory = sqlite3.Row
    return conn
