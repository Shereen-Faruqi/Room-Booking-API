import sqlite3

from app import migrate


def test_up_then_down_round_trip(tmp_path):
    # Uses its own throwaway migration files, so it never depends on the real migrations/ folder.
    (tmp_path / "001_things.up.sql").write_text("CREATE TABLE things (id INTEGER PRIMARY KEY);")
    (tmp_path / "001_things.down.sql").write_text("DROP TABLE things;")
    conn = sqlite3.connect(":memory:")

    def tables():
        rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        return {row[0] for row in rows}

    assert migrate.up(conn, tmp_path) == ["001_things"]
    assert "things" in tables()

    assert migrate.up(conn, tmp_path) == []  # already applied, so nothing to do

    assert migrate.down(conn, 1, tmp_path) == ["001_things"]
    assert "things" not in tables()

    assert migrate.up(conn, tmp_path) == ["001_things"]  # and it can be applied again
    assert "things" in tables()
