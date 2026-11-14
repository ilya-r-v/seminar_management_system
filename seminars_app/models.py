"""Модели приложения «Семинары» (Django ORM)."""

from django.db import models
from django.db.models import Case, Count, F, Q, Value, When
from django.urls import reverse
from django.utils.text import slugify
from unidecode import unidecode

from seminars_app.validators import validate_places

# С какого числа мест семинар считается крупным.
LARGE_SEMINAR_PLACES = 30


def make_base_slug(title):
    """Сделать из названия основу slug: латиница, цифры и дефисы."""
    # Сначала русские буквы переводятся в латиницу,
    # затем строка приводится к виду, пригодному для адреса.
    return slugify(unidecode(title)) or "seminar"


class SeminarQuerySet(models.QuerySet):
    """Дополнительные запросы для семинаров."""

    def with_places(self):
        """Добавить к каждому семинару число занятых и свободных мест.

        Считаются только активные регистрации: отменённые и
        завершённые места не занимают.
        Условие стоит внутри Count, а не в filter(), поэтому семинары
        без регистраций остаются в выборке со значением 0
        (аналог LEFT JOIN + GROUP BY из ПР7).
        """
        # Импорт внутри метода: модель Registration сама импортирует
        # Seminar, поэтому импорт в начале файла был бы циклическим.
        from registrations_app.models import Registration

        return self.annotate(
            registered_count=Count(
                "registrations",
                filter=Q(
                    registrations__status=Registration.Status.ACTIVE
                ),
            ),
        ).annotate(
            free_places=F("max_participants") - F("registered_count"),
        )


class Seminar(models.Model):
    """Семинар."""

    # Название семинара.
    title = models.CharField(
        max_length=200,
        verbose_name="Название",
    )

    # Дата проведения. DateField хранит дату, а не произвольную строку.
    seminar_date = models.DateField(
        verbose_name="Дата проведения",
    )

    # Максимальное число участников (неотрицательное целое).
    max_participants = models.PositiveIntegerField(
        verbose_name="Максимум участников",
        # Дополнительная проверка: мест должно быть не меньше одного.
        validators=[validate_places],
        help_text=(
            "Укажите, сколько человек может зарегистрироваться "
            "на семинар."
        ),
    )

    # Признак «крупный семинар». Значение вычисляет сама база данных
    # по полю max_participants, вручную его задать нельзя.
    is_large = models.GeneratedField(
        expression=Case(
            When(
                max_participants__gte=LARGE_SEMINAR_PLACES,
                then=Value(True),
            ),
            default=Value(False),
            output_field=models.BooleanField(),
        ),
        output_field=models.BooleanField(),
        # Вычисленное значение хранится в таблице.
        db_persist=True,
        verbose_name="Крупный семинар",
    )

    # Изображение семинара (афиша). В базе хранится путь к файлу,
    # сам файл сохраняется в каталоге media/seminars/.
    # Поле необязательное: семинар можно создать без изображения.
    image = models.ImageField(
        upload_to="seminars/",
        blank=True,
        null=True,
        verbose_name="Изображение",
        help_text="Афиша или фотография семинара (необязательно).",
    )

    # Текстовый идентификатор для адреса страницы: /seminars/<slug>/.
    slug = models.SlugField(
        max_length=220,
        unique=True,
        editable=False,
        verbose_name="URL-идентификатор",
    )

    # Менеджер с дополнительным методом with_places().
    objects = SeminarQuerySet.as_manager()

    class Meta:
        # Сортировка по умолчанию: по дате, затем по идентификатору.
        ordering = ["seminar_date", "pk"]
        verbose_name = "Семинар"
        verbose_name_plural = "Семинары"

    def __str__(self):
        # Текстовое представление в админке и Django shell.
        return self.title

    def save(self, *args, **kwargs):
        """Сохранить семинар; при первом сохранении создать slug."""
        # Если slug уже есть, адрес страницы не меняется.
        if not self.slug:
            base_slug = make_base_slug(self.title)
            if self.pk:
                # У существующей записи идентификатор уже известен.
                self.slug = f"{base_slug}-{self.pk}"
            else:
                # Новая запись: сначала сохраняем, чтобы база
                # присвоила идентификатор, затем дописываем slug.
                super().save(*args, **kwargs)
                self.slug = f"{base_slug}-{self.pk}"
                super().save(update_fields=["slug"])
                return
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Адрес страницы семинара на сайте."""
        # reverse() строит адрес по имени маршрута и значению slug.
        return reverse("seminars:detail", kwargs={"slug": self.slug})


class Talk(models.Model):
    """Доклад в программе семинара."""

    # Семинар, к которому относится доклад.
    # CASCADE: доклад не существует без семинара и удаляется вместе с ним.
    seminar = models.ForeignKey(
        Seminar,
        on_delete=models.CASCADE,
        related_name="talks",
        verbose_name="Семинар",
    )

    # Название доклада.
    title = models.CharField(
        max_length=200,
        verbose_name="Название доклада",
    )

    # Докладчик.
    speaker = models.CharField(
        max_length=200,
        verbose_name="Докладчик",
    )

    # Время начала доклада.
    start_time = models.TimeField(
        verbose_name="Время начала",
    )

    # Длительность доклада в минутах.
    duration_minutes = models.PositiveIntegerField(
        verbose_name="Длительность, мин",
    )

    class Meta:
        # Сортировка по умолчанию: по времени начала.
        ordering = ["start_time", "pk"]
        verbose_name = "Доклад"
        verbose_name_plural = "Доклады"

    def __str__(self):
        return f"{self.title} ({self.speaker})"
