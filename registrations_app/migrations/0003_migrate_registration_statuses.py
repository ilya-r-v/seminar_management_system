"""Перенос данных: признак is_cancelled превращается в статус."""

from django.db import migrations


def migrate_registration_statuses(apps, schema_editor):
    """Заполнить status по значению старого поля is_cancelled."""
    # Историческая модель: такая, какой она была на момент миграции.
    Registration = apps.get_model("registrations_app", "Registration")

    # Отменённые регистрации сохраняют свой смысл.
    Registration.objects.filter(is_cancelled=True).update(
        status="cancelled"
    )
    # Все остальные считаются активными.
    Registration.objects.filter(is_cancelled=False).update(
        status="active"
    )


def reverse_registration_statuses(apps, schema_editor):
    """Откат: восстановить is_cancelled по статусу."""
    Registration = apps.get_model("registrations_app", "Registration")

    Registration.objects.filter(status="cancelled").update(
        is_cancelled=True
    )
    Registration.objects.exclude(status="cancelled").update(
        is_cancelled=False
    )


class Migration(migrations.Migration):

    dependencies = [
        ("registrations_app", "0002_registration_status"),
    ]

    operations = [
        migrations.RunPython(
            migrate_registration_statuses,
            reverse_registration_statuses,
        ),
    ]
