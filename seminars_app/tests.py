"""Тесты приложения «Семинары»: модели, ORM-запросы и страницы."""

from datetime import date, time

from django.test import TestCase
from django.urls import reverse

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.models import Seminar, Talk


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
        self.assertTrue(response.context["error"])

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
