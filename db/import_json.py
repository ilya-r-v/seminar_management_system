"""Перенос данных проекта из JSON-файлов каталога data/ в SQLite.

Запуск из корня проекта:
    python3 -m db.import_json

Скрипт можно запускать повторно: перед загрузкой таблицы очищаются,
поэтому база всегда совпадает с текущим содержимым JSON-файлов.
"""

import json
import sqlite3
from pathlib import Path
from typing import Any, List, Optional

from db.database import DATA_DIR, get_connection, init_db


def load_json(file_path: Path) -> List[Any]:
    """Прочитать JSON-файл и вернуть список записей."""
    with open(file_path, encoding="utf-8") as file:
        return json.load(file)


def clear_tables(conn: sqlite3.Connection) -> None:
    """Очистить таблицы (сначала зависимые, затем основные)."""
    for table in ("registrations", "talks", "participants", "seminars"):
        conn.execute(f"DELETE FROM {table}")


def import_seminars(conn: sqlite3.Connection, data_dir: Path) -> None:
    """Перенести семинары в таблицу seminars."""
    seminars = load_json(data_dir / "seminars.json")
    conn.executemany(
        """
        INSERT INTO seminars (
            id,
            title,
            seminar_date,
            max_participants
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                seminar["id"],
                seminar["title"],
                seminar["date"],
                seminar["max_participants"],
            )
            for seminar in seminars
        ],
    )


def import_participants(conn: sqlite3.Connection, data_dir: Path) -> None:
    """Перенести участников в таблицу participants."""
    participants = load_json(data_dir / "participants.json")
    conn.executemany(
        """
        INSERT INTO participants (
            id,
            name,
            email
        )
        VALUES (?, ?, ?)
        """,
        [
            (
                participant["id"],
                participant["name"],
                participant["email"],
            )
            for participant in participants
        ],
    )


def import_registrations(conn: sqlite3.Connection, data_dir: Path) -> None:
    """Перенести регистрации в таблицу registrations."""
    registrations = load_json(data_dir / "registrations.json")
    conn.executemany(
        """
        INSERT INTO registrations (
            id,
            seminar_id,
            participant_id,
            is_cancelled
        )
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                registration["id"],
                registration["seminar_id"],
                registration["participant_id"],
                int(registration["is_cancelled"]),
            )
            for registration in registrations
        ],
    )


def import_talks(conn: sqlite3.Connection, data_dir: Path) -> None:
    """Перенести доклады в таблицу talks."""
    talks = load_json(data_dir / "talks.json")
    conn.executemany(
        """
        INSERT INTO talks (
            id,
            seminar_id,
            title,
            speaker,
            start_time,
            duration_minutes
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                talk["id"],
                talk["seminar_id"],
                talk["title"],
                talk["speaker"],
                talk["start_time"],
                talk["duration_minutes"],
            )
            for talk in talks
        ],
    )


def import_all(conn: sqlite3.Connection, data_dir: Path = DATA_DIR) -> None:
    """Очистить таблицы и загрузить в них данные из JSON-файлов.

    Порядок важен: сначала таблицы, на которые ссылаются внешние ключи
    (seminars, participants), затем registrations и talks.
    """
    clear_tables(conn)
    import_seminars(conn, data_dir)
    import_participants(conn, data_dir)
    import_registrations(conn, data_dir)
    import_talks(conn, data_dir)


def main(db_path: Optional[Path] = None) -> None:
    """Создать базу (если её нет) и перенести в неё данные из JSON."""
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        import_all(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
