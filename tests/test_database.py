"""Тесты слоя базы данных SQLite (db/ и sql/)."""

import json
import sqlite3
from pathlib import Path

import pytest

from db.database import DATA_DIR, get_connection, init_db
from db.import_json import import_all

QUERIES_FILE = Path(__file__).resolve().parent.parent / "sql" / "queries.sql"
TABLES = ["seminars", "participants", "registrations", "talks"]


@pytest.fixture
def conn(tmp_path):
    """Пустая база во временном каталоге с созданной схемой."""
    db_path = tmp_path / "test.sqlite"
    init_db(db_path)
    connection = get_connection(db_path)
    yield connection
    connection.close()


def count_rows(connection, table):
    return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_schema_creates_all_tables(conn):
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table'"
    ).fetchall()
    assert {row["name"] for row in rows} >= set(TABLES)


def test_registrations_have_foreign_keys(conn):
    rows = conn.execute("PRAGMA foreign_key_list(registrations)").fetchall()
    assert {row["table"] for row in rows} == {"seminars", "participants"}


def test_foreign_key_is_enforced(conn):
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO registrations "
            "(id, seminar_id, participant_id, is_cancelled) "
            "VALUES (1, 999, 999, 0)"
        )


def test_rows_are_accessible_by_name(conn):
    conn.execute(
        "INSERT INTO seminars (id, title, seminar_date, max_participants) "
        "VALUES (1, 'Python', '2026-10-01', 5)"
    )
    row = conn.execute("SELECT * FROM seminars").fetchone()
    assert row["title"] == "Python"
    assert row["max_participants"] == 5


def test_import_copies_all_json_records(conn):
    import_all(conn)
    for table in TABLES:
        json_file = DATA_DIR / f"{table}.json"
        with open(json_file, encoding="utf-8") as file:
            expected = len(json.load(file))
        assert count_rows(conn, table) == expected


def test_import_can_be_repeated(conn):
    import_all(conn)
    import_all(conn)
    with open(DATA_DIR / "seminars.json", encoding="utf-8") as file:
        assert count_rows(conn, "seminars") == len(json.load(file))


def test_queries_file_runs_without_errors(conn):
    import_all(conn)
    conn.executescript(QUERIES_FILE.read_text(encoding="utf-8"))
