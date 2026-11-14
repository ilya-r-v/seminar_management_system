"""Тесты приложения «Семинары»: модели, ORM-запросы и страницы."""

import io
import shutil
import tempfile
from datetime import date, time, timedelta
from pathlib import Path

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import resolve, reverse
from django.utils import timezone
from django.views.static import serve
from PIL import Image

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.forms import SeminarForm
from seminars_app.models import Seminar, Talk
from seminars_app.validators import validate_places


class SeminarTestData(TestCase):
    """Общие тестовые данные: два семинара, два участника."""

    @classmethod
    def setUpTestData(cls):
        cls.django = Seminar.objects.create(
            title="Django ORM",
            seminar_date=date(2026, 9, 21),
            max_participants=1,
        )
        cls.python = Seminar.objects.create(
            title="Python",
            seminar_date=date(2026, 10, 12),
            max_participants=3,
        )
        cls.anna = Participant.objects.create(
            name="Anna", email="anna@example.com"
        )
        cls.boris = Participant.objects.create(
            name="Boris", email="boris@example.com"
        )
        # Семинар Django ORM занят полностью одной активной регистрацией.
        Registration.objects.create(
            seminar=cls.django, participant=cls.anna
        )
        # Отменённая регистрация место не занимает.
        Registration.objects.create(
            seminar=cls.python,
            participant=cls.boris,
            status=Registration.Status.CANCELLED,
        )
        Talk.objects.create(
            seminar=cls.django,
            title="Models",
            speaker="Anna",
            start_time=time(12, 15),
            duration_minutes=10,
        )


class SeminarQueryTests(SeminarTestData):
    """Проверка запроса with_places()."""

    def test_counts_only_active_registrations(self):
        seminar = Seminar.objects.with_places().get(pk=self.python.pk)
        self.assertEqual(seminar.registered_count, 0)
        self.assertEqual(seminar.free_places, 3)

    def test_seminar_without_registrations_is_kept(self):
        empty = Seminar.objects.create(
            title="Empty",
            seminar_date=date(2026, 11, 1),
            max_participants=5,
        )
        ids = Seminar.objects.with_places().values_list("pk", flat=True)
        self.assertIn(empty.pk, ids)

    def test_reverse_relation_returns_talks(self):
        self.assertEqual(self.django.talks.count(), 1)


class SeminarPageTests(SeminarTestData):
    """Проверка страниц семинаров."""

    def test_list_shows_all_seminars(self):
        response = self.client.get(reverse("seminars:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["seminar_items"]), 2)

    def test_list_search_by_title(self):
        response = self.client.get(reverse("seminars:list"), {"q": "pyth"})
        titles = [item.title for item in response.context["seminar_items"]]
        self.assertEqual(titles, ["Python"])

    def test_detail_shows_program_and_participants(self):
        response = self.client.get(self.django.get_absolute_url())
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Models")
        self.assertContains(response, "12:15")
        self.assertContains(response, "anna@example.com")
        self.assertContains(response, "Мест нет")

    def test_detail_of_missing_seminar_returns_404(self):
        response = self.client.get(
            reverse("seminars:detail", kwargs={"slug": "net-takogo-999"})
        )
        self.assertEqual(response.status_code, 404)

    def test_available_excludes_full_seminar(self):
        response = self.client.get(
            reverse("seminars:available"), {"date": "2026-09-01"}
        )
        titles = [item.title for item in response.context["seminars"]]
        self.assertEqual(titles, ["Python"])

    def test_available_respects_date(self):
        response = self.client.get(
            reverse("seminars:available"), {"date": "2026-12-01"}
        )
        self.assertEqual(len(response.context["seminars"]), 0)

    def test_cancelled_registration_frees_place(self):
        Registration.objects.get(seminar=self.django).cancel()
        response = self.client.get(
            reverse("seminars:available"), {"date": "2026-09-01"}
        )
        self.assertEqual(len(response.context["seminars"]), 2)

    def test_available_reports_wrong_date(self):
        response = self.client.get(
            reverse("seminars:available"), {"date": "не-дата"}
        )
        self.assertEqual(response.status_code, 200)
        # Ошибка относится к полю date формы, поиск не выполняется.
        self.assertIn("date", response.context["form"].errors)
        self.assertEqual(len(response.context["seminars"]), 0)
        self.assertContains(response, "Укажите дату в формате")

    def test_home_page_counts(self):
        response = self.client.get(reverse("homepage:index"))
        self.assertEqual(response.context["seminars_total"], 2)
        self.assertEqual(response.context["participants_count"], 2)
        self.assertEqual(response.context["active_registrations_count"], 1)


class SeminarSlugTests(SeminarTestData):
    """Проверка slug, get_absolute_url() и адресов страниц."""

    def test_slug_is_made_from_russian_title(self):
        seminar = Seminar.objects.create(
            title="Основы Django ORM",
            seminar_date=date(2026, 11, 20),
            max_participants=10,
        )
        self.assertEqual(seminar.slug, f"osnovy-django-orm-{seminar.pk}")

    def test_slug_does_not_change_after_rename(self):
        old_slug = self.django.slug
        self.django.title = "Новое название"
        self.django.save()
        self.django.refresh_from_db()
        self.assertEqual(self.django.slug, old_slug)

    def test_slugs_are_unique_for_same_titles(self):
        twin = Seminar.objects.create(
            title="Django ORM",
            seminar_date=date(2026, 12, 1),
            max_participants=5,
        )
        self.assertNotEqual(twin.slug, self.django.slug)

    def test_title_without_letters_gets_default_slug(self):
        seminar = Seminar.objects.create(
            title="!!!",
            seminar_date=date(2026, 12, 1),
            max_participants=5,
        )
        self.assertEqual(seminar.slug, f"seminar-{seminar.pk}")

    def test_get_absolute_url(self):
        self.assertEqual(
            self.django.get_absolute_url(),
            f"/seminars/{self.django.slug}/",
        )

    def test_list_links_use_slug(self):
        response = self.client.get(reverse("seminars:list"))
        self.assertContains(response, self.django.get_absolute_url())

    def test_old_address_redirects_to_slug(self):
        response = self.client.get(f"/seminars/{self.django.pk}/")
        self.assertRedirects(response, self.django.get_absolute_url())

    def test_old_address_of_missing_seminar_returns_404(self):
        response = self.client.get("/seminars/9999/")
        self.assertEqual(response.status_code, 404)


class SeminarGeneratedFieldTests(TestCase):
    """Проверка вычисляемого поля is_large."""

    def make_seminar(self, places):
        seminar = Seminar.objects.create(
            title="Seminar",
            seminar_date=date(2026, 11, 20),
            max_participants=places,
        )
        seminar.refresh_from_db()
        return seminar

    def test_small_seminar(self):
        self.assertFalse(self.make_seminar(29).is_large)

    def test_large_seminar(self):
        self.assertTrue(self.make_seminar(30).is_large)

    def test_value_is_recalculated(self):
        seminar = self.make_seminar(5)
        seminar.max_participants = 100
        seminar.save()
        seminar.refresh_from_db()
        self.assertTrue(seminar.is_large)

    def test_filter_by_generated_field(self):
        self.make_seminar(5)
        self.make_seminar(50)
        self.assertEqual(Seminar.objects.filter(is_large=True).count(), 1)


class RegistrationStatusPlacesTests(SeminarTestData):
    """Места занимают только активные регистрации."""

    def test_completed_registration_frees_place(self):
        registration = Registration.objects.get(seminar=self.django)
        registration.status = Registration.Status.COMPLETED
        registration.save()
        seminar = Seminar.objects.with_places().get(pk=self.django.pk)
        self.assertEqual(seminar.registered_count, 0)
        response = self.client.get(
            reverse("seminars:available"), {"date": "2026-09-01"}
        )
        self.assertEqual(len(response.context["seminars"]), 2)


class ContextProcessorTests(SeminarTestData):
    """Общие данные доступны на разных страницах."""

    def test_site_name_and_total_on_every_page(self):
        addresses = [
            reverse("homepage:index"),
            reverse("seminars:list"),
            reverse("registrations:list"),
            reverse("registrations:statistics"),
        ]
        for address in addresses:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(
                    response.context["site_name"],
                    "Система управления семинарами",
                )
                self.assertEqual(response.context["seminars_total"], 2)
                self.assertContains(response, "Семинары (2)")

    def test_total_changes_with_data(self):
        Seminar.objects.create(
            title="Third",
            seminar_date=date(2026, 12, 1),
            max_participants=5,
        )
        response = self.client.get(reverse("homepage:index"))
        self.assertContains(response, "Семинары (3)")


class QueryCountTests(SeminarTestData):
    """Число SQL-запросов не растёт вместе с числом записей."""

    def add_seminars(self, count):
        for number in range(count):
            seminar = Seminar.objects.create(
                title=f"Extra {number}",
                seminar_date=date(2026, 12, 1),
                max_participants=5,
            )
            Registration.objects.create(
                seminar=seminar, participant=self.anna
            )

    def test_seminar_list_queries(self):
        self.add_seminars(10)
        # 1 — список семинаров с подсчётом мест,
        # 2 — число семинаров в навигации (контекстный процессор).
        with self.assertNumQueries(2):
            self.client.get(reverse("seminars:list"))

    def test_seminar_detail_queries(self):
        # Семинар, доклады, участники и число семинаров в навигации.
        with self.assertNumQueries(4):
            self.client.get(self.django.get_absolute_url())


def make_image(name="poster.png"):
    """Создать в памяти маленькое настоящее изображение PNG."""
    buffer = io.BytesIO()
    Image.new("RGB", (4, 4), "navy").save(buffer, format="PNG")
    return SimpleUploadedFile(
        name, buffer.getvalue(), content_type="image/png"
    )


class SeminarSearchFormTests(SeminarTestData):
    """Поиск семинаров через форму SeminarSearchForm."""

    def test_empty_request_gives_unbound_form(self):
        response = self.client.get(reverse("seminars:list"))
        self.assertFalse(response.context["form"].is_bound)

    def test_query_is_kept_in_form(self):
        response = self.client.get(reverse("seminars:list"), {"q": "pyth"})
        self.assertEqual(response.context["form"].cleaned_data["q"], "pyth")
        self.assertContains(response, 'value="pyth"')

    def test_too_long_query_is_rejected(self):
        response = self.client.get(
            reverse("seminars:list"), {"q": "x" * 300}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("q", response.context["form"].errors)
        # При ошибке показывается полный список.
        self.assertEqual(len(response.context["seminar_items"]), 2)


class AvailableSeminarsFormTests(SeminarTestData):
    """Поиск свободных мест через форму AvailableSeminarsForm."""

    def test_empty_request_shows_no_errors(self):
        response = self.client.get(reverse("seminars:available"))
        self.assertFalse(response.context["form"].is_bound)
        self.assertNotContains(response, "form-error")

    def test_date_is_converted_to_date_object(self):
        response = self.client.get(
            reverse("seminars:available"), {"date": "2026-09-01"}
        )
        self.assertEqual(response.context["selected_date"], date(2026, 9, 1))
        self.assertContains(response, "Начиная с 01.09.2026")


class SeminarFormTests(TestCase):
    """Проверка самой формы SeminarForm."""

    def make_data(self, **changes):
        data = {
            "title": "Новый семинар",
            "seminar_date": timezone.localdate() + timedelta(days=5),
            "max_participants": 10,
        }
        data.update(changes)
        return data

    def test_form_has_only_allowed_fields(self):
        self.assertEqual(
            list(SeminarForm().fields),
            ["title", "seminar_date", "max_participants", "image"],
        )

    def test_valid_data_without_image(self):
        self.assertTrue(SeminarForm(self.make_data()).is_valid())

    def test_today_is_allowed(self):
        form = SeminarForm(
            self.make_data(seminar_date=timezone.localdate())
        )
        self.assertTrue(form.is_valid())

    def test_past_date_is_field_error(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        form = SeminarForm(self.make_data(seminar_date=yesterday))
        self.assertFalse(form.is_valid())
        self.assertIn("прошедшую дату", form.errors["seminar_date"][0])

    def test_validator_rejects_zero_places(self):
        form = SeminarForm(self.make_data(max_participants=0))
        self.assertFalse(form.is_valid())
        self.assertIn(
            "не меньше одного", form.errors["max_participants"][0]
        )

    def test_validator_function(self):
        validate_places(1)
        with self.assertRaises(ValidationError):
            validate_places(0)

    def test_negative_places_are_rejected(self):
        form = SeminarForm(self.make_data(max_participants=-3))
        self.assertFalse(form.is_valid())
        self.assertIn("max_participants", form.errors)

    def test_blank_title_is_rejected(self):
        form = SeminarForm(self.make_data(title="   "))
        self.assertFalse(form.is_valid())
        self.assertIn("title", form.errors)

    def test_not_an_image_is_rejected(self):
        fake = SimpleUploadedFile(
            "notes.png", b"this is not an image", content_type="image/png"
        )
        form = SeminarForm(self.make_data(), {"image": fake})
        self.assertFalse(form.is_valid())
        self.assertIn("image", form.errors)


class SeminarFormPageTests(TestCase):
    """Создание и редактирование семинара, загрузка изображения."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Загруженные в тестах файлы пишутся во временный каталог,
        # а не в настоящий каталог media/ проекта.
        cls.media_dir = tempfile.mkdtemp()
        cls.media_override = override_settings(MEDIA_ROOT=cls.media_dir)
        cls.media_override.enable()

    @classmethod
    def tearDownClass(cls):
        cls.media_override.disable()
        shutil.rmtree(cls.media_dir, ignore_errors=True)
        super().tearDownClass()

    def make_data(self, **changes):
        data = {
            "title": "Основы Django",
            "seminar_date": (
                timezone.localdate() + timedelta(days=5)
            ).isoformat(),
            "max_participants": 10,
        }
        data.update(changes)
        return data

    def test_get_shows_empty_form_for_files(self):
        response = self.client.get(reverse("seminars:create"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_create_without_image(self):
        response = self.client.post(
            reverse("seminars:create"), self.make_data()
        )
        seminar = Seminar.objects.get()
        self.assertRedirects(response, seminar.get_absolute_url())
        self.assertEqual(seminar.slug, f"osnovy-django-{seminar.pk}")
        self.assertFalse(seminar.image)
        page = self.client.get(seminar.get_absolute_url())
        self.assertContains(page, "Изображение не загружено.")

    def test_create_with_image(self):
        self.client.post(
            reverse("seminars:create"),
            self.make_data(image=make_image()),
        )
        seminar = Seminar.objects.get()
        # В базе хранится путь, файл лежит в каталоге медиафайлов.
        self.assertTrue(seminar.image.name.startswith("seminars/"))
        self.assertTrue(Path(seminar.image.path).exists())
        page = self.client.get(seminar.get_absolute_url())
        self.assertContains(page, seminar.image.url)
        # Адрес изображения начинается с MEDIA_URL и обслуживается
        # маршрутом раздачи медиафайлов.
        self.assertTrue(seminar.image.url.startswith("/media/seminars/"))
        self.assertEqual(resolve(seminar.image.url).func, serve)

    def test_invalid_post_saves_nothing(self):
        response = self.client.post(
            reverse("seminars:create"),
            self.make_data(max_participants=0, seminar_date="не дата"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["form"].errors),
            {"max_participants", "seminar_date"},
        )
        # Введённое название остаётся в форме.
        self.assertContains(response, "Основы Django")
        self.assertEqual(Seminar.objects.count(), 0)

    def test_post_without_csrf_token_is_forbidden(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(reverse("seminars:create"), self.make_data())
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Seminar.objects.count(), 0)

    def test_update_changes_existing_record(self):
        self.client.post(reverse("seminars:create"), self.make_data())
        seminar = Seminar.objects.get()
        address = reverse("seminars:update", args=[seminar.slug])

        page = self.client.get(address)
        self.assertEqual(page.context["form"].instance, seminar)
        self.assertContains(page, "Сохранить изменения")

        response = self.client.post(
            address,
            self.make_data(max_participants=40, image=make_image("new.png")),
        )
        self.assertRedirects(response, seminar.get_absolute_url())
        self.assertEqual(Seminar.objects.count(), 1)
        seminar.refresh_from_db()
        self.assertEqual(seminar.max_participants, 40)
        self.assertTrue(seminar.is_large)
        self.assertIn("new", seminar.image.name)

    def test_past_seminar_can_be_edited_without_changing_date(self):
        past = Seminar.objects.create(
            title="Прошедший",
            seminar_date=date(2020, 1, 15),
            max_participants=5,
        )
        response = self.client.post(
            reverse("seminars:update", args=[past.slug]),
            self.make_data(title="Прошедший", seminar_date="2020-01-15"),
        )
        self.assertEqual(response.status_code, 302)
        # Но перенести его на другую прошедшую дату нельзя.
        response = self.client.post(
            reverse("seminars:update", args=[past.slug]),
            self.make_data(title="Прошедший", seminar_date="2020-02-01"),
        )
        self.assertContains(response, "прошедшую дату")

    def test_update_of_missing_seminar_returns_404(self):
        response = self.client.get(
            reverse("seminars:update", args=["net-takogo-999"])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_page_links(self):
        self.client.post(reverse("seminars:create"), self.make_data())
        seminar = Seminar.objects.get()
        page = self.client.get(seminar.get_absolute_url())
        self.assertContains(
            page, reverse("seminars:update", args=[seminar.slug])
        )
        self.assertContains(
            page,
            reverse("registrations:create") + f"?seminar={seminar.pk}",
        )

    def test_create_route_is_not_taken_for_slug(self):
        self.assertEqual(
            self.client.get("/seminars/create/").status_code, 200
        )
