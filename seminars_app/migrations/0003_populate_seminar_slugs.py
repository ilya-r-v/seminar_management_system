"""Перенос данных: заполнение slug у уже существующих семинаров."""

from django.db import migrations
from django.utils.text import slugify
from unidecode import unidecode


def populate_seminar_slugs(apps, schema_editor):
    """Сформировать slug из названия и идентификатора семинара."""
    # Историческая модель: такая, какой она была на момент миграции.
    Seminar = apps.get_model("seminars_app", "Seminar")

    for seminar in Seminar.objects.order_by("pk"):
        # Русское название переводится в латиницу и приводится
        # к виду, пригодному для адреса страницы.
        base_slug = slugify(unidecode(seminar.title)) or "seminar"
        # Идентификатор в конце гарантирует уникальность.
        seminar.slug = f"{base_slug}-{seminar.pk}"
        seminar.save(update_fields=["slug"])


class Migration(migrations.Migration):

    dependencies = [
        ("seminars_app", "0002_seminar_is_large_slug"),
    ]

    operations = [
        migrations.RunPython(
            populate_seminar_slugs,
            migrations.RunPython.noop,
        ),
    ]
