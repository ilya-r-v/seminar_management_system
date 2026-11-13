"""Перенос данных из базы ПР7 в базу Django (через ORM).

Источник: data/seminars.sqlite (только чтение).
Приёмник: db.sqlite3 — база из настройки DATABASES.

Перед запуском нужно применить миграции: python manage.py migrate
Запуск из корня проекта: python db/import_sqlite_to_orm.py
"""

import os
import sqlite3
import sys
from datetime import date, time
from pathlib import Path

import django
from django.db import transaction

# Корень проекта: скрипт лежит в подкаталоге db.
BASE_DIR = Path(__file__).resolve().parent.parent

# Добавляем корень проекта в пути поиска модулей,
# чтобы найти пакет настроек при запуске из каталога db.
sys.path.insert(0, str(BASE_DIR))

# Исходная база, созданная в ПР7.
SOURCE_DB = BASE_DIR / "data" / "seminars.sqlite"

# Модуль настроек Django.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "seminar_site.settings")


def read_source(source_db):
    """Прочитать все строки исходной базы."""
    with sqlite3.connect(source_db) as connection:
        connection.row_factory = sqlite3.Row
        seminars = connection.execute(
            """
            SELECT id, title, seminar_date, max_participants
            FROM seminars
            ORDER BY id
            """
        ).fetchall()
        participants = connection.execute(
            """
            SELECT id, name, email
            FROM participants
            ORDER BY id
            """
        ).fetchall()
        registrations = connection.execute(
            """
            SELECT id, seminar_id, participant_id, is_cancelled
            FROM registrations
            ORDER BY id
            """
        ).fetchall()
        talks = connection.execute(
            """
            SELECT
                id,
                seminar_id,
                title,
                speaker,
                start_time,
                duration_minutes
            FROM talks
            ORDER BY id
            """
        ).fetchall()
    return seminars, participants, registrations, talks


def import_data(source_db=SOURCE_DB):
    """Перенести данные из исходной базы в модели Django."""
    # Модели импортируются только после django.setup().
    from participants_app.models import Participant
    from registrations_app.models import Registration
    from seminars_app.models import Seminar, Talk

    if not Path(source_db).exists():
        raise FileNotFoundError(f"Исходная база не найдена: {source_db}")

    seminars, participants, registrations, talks = read_source(source_db)

    # Одна транзакция: при ошибке все изменения откатываются.
    with transaction.atomic():
        # Сначала независимые сущности: семинары и участники.
        for row in seminars:
            Seminar.objects.update_or_create(
                # Сохраняем исходный первичный ключ.
                pk=row["id"],
                defaults={
                    "title": row["title"],
                    # Строка ГГГГ-ММ-ДД превращается в объект date.
                    "seminar_date": date.fromisoformat(
                        row["seminar_date"]
                    ),
                    "max_participants": row["max_participants"],
                },
            )

        for row in participants:
            Participant.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "name": row["name"],
                    "email": row["email"],
                },
            )

        # Затем сущности, которые ссылаются на них внешними ключами.
        for row in registrations:
            # Признак отмены 0/1 превращается в статус регистрации.
            if row["is_cancelled"]:
                status = Registration.Status.CANCELLED
            else:
                status = Registration.Status.ACTIVE
            defaults = {
                "seminar_id": row["seminar_id"],
                "participant_id": row["participant_id"],
                "status": status,
            }
            # В исходной базе нет статуса «завершена». Если регистрацию
            # завершили уже в Django, повторный перенос его не сбрасывает.
            completed = Registration.objects.completed().filter(
                pk=row["id"]
            )
            if not row["is_cancelled"] and completed.exists():
                del defaults["status"]
            Registration.objects.update_or_create(
                pk=row["id"],
                defaults=defaults,
            )

        for row in talks:
            Talk.objects.update_or_create(
                pk=row["id"],
                defaults={
                    "seminar_id": row["seminar_id"],
                    "title": row["title"],
                    "speaker": row["speaker"],
                    # Строка ЧЧ:ММ превращается в объект time.
                    "start_time": time.fromisoformat(row["start_time"]),
                    "duration_minutes": row["duration_minutes"],
                },
            )

    # Количество записей в целевой базе —
    # его нужно сверить с результатом inspect_source_db.py.
    print("Перенос данных завершён.")
    print(f"Семинаров: {Seminar.objects.count()}")
    print(f"Участников: {Participant.objects.count()}")
    print(f"Регистраций: {Registration.objects.count()}")
    print(f"Докладов: {Talk.objects.count()}")


if __name__ == "__main__":
    # Инициализируем Django и запускаем перенос
    # только при прямом выполнении файла.
    django.setup()
    import_data()
