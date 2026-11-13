"""Просмотр структуры исходной базы ПР7 (data/seminars.sqlite).

Скрипт только читает базу: выводит таблицы, столбцы и число записей.
Запуск из корня проекта: python db/inspect_source_db.py
"""

import sqlite3
from pathlib import Path

# Корень проекта: скрипт лежит в подкаталоге db.
BASE_DIR = Path(__file__).resolve().parent.parent

# Исходная база, созданная в ПР7.
SOURCE_DB = BASE_DIR / "data" / "seminars.sqlite"


def main():
    """Вывести описание всех таблиц исходной базы."""
    if not SOURCE_DB.exists():
        raise FileNotFoundError(f"Исходная база не найдена: {SOURCE_DB}")

    with sqlite3.connect(SOURCE_DB) as connection:
        # Обращение к значениям строк по именам столбцов.
        connection.row_factory = sqlite3.Row

        # Список пользовательских таблиц.
        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()

        for (table_name,) in tables:
            print(f"\nТаблица: {table_name}")

            # Описание столбцов: имя, тип, NOT NULL, первичный ключ.
            columns = connection.execute(
                f'PRAGMA table_info("{table_name}")'
            ).fetchall()
            print("Столбцы:")
            for column in columns:
                print(
                    f"  имя={column['name']}, "
                    f"тип={column['type']}, "
                    f"NOT NULL={column['notnull']}, "
                    f"PRIMARY KEY={column['pk']}"
                )

            # Количество записей в таблице.
            count = connection.execute(
                f'SELECT COUNT(*) FROM "{table_name}"'
            ).fetchone()[0]
            print(f"Количество записей: {count}")


if __name__ == "__main__":
    main()
