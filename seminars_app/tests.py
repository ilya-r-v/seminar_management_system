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
            seminar=cls.python, participant=cls.boris, is_cancelled=True
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
        response = self.client.get(
            reverse("seminars:detail", args=[self.django.pk])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Models")
        self.assertContains(response, "12:15")
        self.assertContains(response, "anna@example.com")
        self.assertContains(response, "Мест нет")

    def test_detail_of_missing_seminar_returns_404(self):
        response = self.client.get(reverse("seminars:detail", args=[9999]))
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
        self.assertEqual(response.context["seminars_count"], 2)
        self.assertEqual(response.context["participants_count"], 2)
        self.assertEqual(response.context["active_registrations_count"], 1)
