"""Подключение к базе данных SQLite проекта и выполнение запросов."""

import sqlite3
from pathlib import Path
from typing import List, Optional, Sequence, Union

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SCHEMA_FILE = BASE_DIR / "sql" / "schema.sql"
DB_PATH = DATA_DIR / "seminars.sqlite"

PathLike = Union[str, Path]


def get_connection(db_path: Optional[PathLike] = None) -> sqlite3.Connection:
    """Создать соединение с базой данных.

    Для соединения настраивается:
    - row_factory = sqlite3.Row: к полям строки результата можно
      обращаться по имени (row["title"], в шаблоне {{ row.title }});
    - PRAGMA foreign_keys = ON: SQLite проверяет внешние ключи
      (по умолчанию эта проверка выключена).
    """
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[PathLike] = None) -> None:
    """Создать файл базы данных и таблицы по схеме sql/schema.sql."""
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()


def fetch_all(
    sql: str, params: Sequence[object] = ()
) -> List[sqlite3.Row]:
    """Выполнить SELECT-запрос и вернуть все строки результата.

    Значения передаются отдельно от текста запроса (заполнители ?),
    поэтому пользовательские данные не могут изменить сам запрос.
    """
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def fetch_one(
    sql: str, params: Sequence[object] = ()
) -> Optional[sqlite3.Row]:
    """Выполнить SELECT-запрос и вернуть первую строку (или None)."""
    conn = get_connection()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()
