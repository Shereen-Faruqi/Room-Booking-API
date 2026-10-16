"""Tiny SQL migration runner.

Migrations live in migrations/ as NNN_name.up.sql and NNN_name.down.sql.
Applied versions are recorded in the schema_migrations table.

Usage:
    python -m app.migrate up         apply all pending migrations
    python -m app.migrate down [N]   undo the last N migrations (default 1)
"""
import re
import sys
from pathlib import Path

from app.db import connect

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
_FILE_NAME = re.compile(r"^(\d+_[A-Za-z0-9_]+)\.(up|down)\.sql$")


class MigrationError(Exception):
    """Raised when a migration cannot be applied or undone."""


def _discover(directory):
    """Return {version: {"up": Path, "down": Path}} for the SQL files found."""
    found = {}
    for path in sorted(Path(directory).glob("*.sql")):
        match = _FILE_NAME.match(path.name)
        if match:
            found.setdefault(match.group(1), {})[match.group(2)] = path
    return found


def _applied(conn):
    """Applied versions, oldest first. Creates the tracking table if needed."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY)")
    conn.commit()
    rows = conn.execute("SELECT version FROM schema_migrations ORDER BY version")
    return [row[0] for row in rows]


def _run(conn, sql, record_sql, version):
    """Run one migration script and its bookkeeping change in one transaction."""
    try:
        conn.executescript("BEGIN;\n" + sql)
        conn.execute(record_sql, (version,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def up(conn, directory=MIGRATIONS_DIR):
    """Apply every pending migration, oldest first. Returns the versions applied."""
    done = set(_applied(conn))
    applied_now = []
    for version, files in sorted(_discover(directory).items()):
        if version in done or "up" not in files:
            continue
        _run(conn, files["up"].read_text(),
             "INSERT INTO schema_migrations (version) VALUES (?)", version)
        applied_now.append(version)
    return applied_now


def down(conn, steps=1, directory=MIGRATIONS_DIR):
    """Undo the last `steps` applied migrations, newest first. Returns the versions undone."""
    if steps < 1:
        raise MigrationError("steps must be at least 1")
    found = _discover(directory)
    reverted = []
    for version in reversed(_applied(conn)[-steps:]):
        files = found.get(version, {})
        if "down" not in files:
            raise MigrationError(f"No down migration found for {version}")
        _run(conn, files["down"].read_text(),
             "DELETE FROM schema_migrations WHERE version = ?", version)
        reverted.append(version)
    return reverted


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    command = args[0] if args else ""
    if command not in ("up", "down"):
        print(__doc__)
        return 2
    conn = connect()
    try:
        if command == "up":
            changed, verb = up(conn), "applied"
        else:
            changed, verb = down(conn, int(args[1]) if len(args) > 1 else 1), "reverted"
    except (MigrationError, ValueError) as error:
        print(f"error: {error}")
        return 1
    finally:
        conn.close()
    for version in changed:
        print(f"{verb} {version}")
    if not changed:
        print("nothing to do")
    return 0


if __name__ == "__main__":
    sys.exit(main())
