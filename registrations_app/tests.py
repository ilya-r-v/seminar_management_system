"""Тесты приложения «Регистрации»: модель, список и статистика."""

import io
import tempfile
from contextlib import redirect_stdout
from datetime import date, time
from pathlib import Path

from django.db.models import ProtectedError
from django.test import TestCase
from django.urls import reverse

from db.database import get_connection, init_db
from db.import_sqlite_to_orm import import_data
from participants_app.models import Participant
from registrations_app.models import Registration
from registrations_app.views import REGISTRATIONS_PER_PAGE
from seminars_app.models import Seminar


class RegistrationTestData(TestCase):
    """Общие тестовые данные: два семинара, три участника."""

    @classmethod
    def setUpTestData(cls):
        cls.django = Seminar.objects.create(
            title="Django ORM",
            seminar_date=date(2026, 9, 21),
            max_participants=2,
        )
        cls.python = Seminar.objects.create(
            title="Python",
            seminar_date=date(2026, 10, 12),
            max_participants=10,
        )
        cls.anna = Participant.objects.create(
            name="Anna", email="anna@example.com"
        )
        cls.boris = Participant.objects.create(
            name="Boris", email="boris@example.com"
        )
        cls.clara = Participant.objects.create(
            name="Clara", email="clara@example.com"
        )
        cls.first = Registration.objects.create(
            seminar=cls.django, participant=cls.anna
        )
        cls.second = Registration.objects.create(
            seminar=cls.python, participant=cls.anna
        )
        cls.cancelled = Registration.objects.create(
            seminar=cls.django, participant=cls.boris, is_cancelled=True
        )

    def get_ids(self, **params):
        """Вернуть id регистраций, показанных на странице списка."""
        response = self.client.get(reverse("registrations:list"), params)
        self.assertEqual(response.status_code, 200)
        return [item["id"] for item in response.context["registrations"]]


class RegistrationModelTests(RegistrationTestData):
    """Проверка модели и связей."""

    def test_cancel_saves_flag(self):
        self.first.cancel()
        self.first.refresh_from_db()
        self.assertTrue(self.first.is_cancelled)

    def test_reverse_relations(self):
        self.assertEqual(self.django.registrations.count(), 2)
        self.assertEqual(self.anna.registrations.count(), 2)

    def test_seminar_with_registrations_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.django.delete()


class RegistrationListTests(RegistrationTestData):
    """Проверка фильтров, поиска, сортировки и страниц."""

    def test_only_active_by_default(self):
        self.assertEqual(
            self.get_ids(), [self.first.pk, self.second.pk]
        )

    def test_status_filter(self):
        self.assertEqual(
            self.get_ids(status="cancelled"), [self.cancelled.pk]
        )
        self.assertEqual(len(self.get_ids(status="all")), 3)
        # Старая ссылка из ПР7.
        self.assertEqual(len(self.get_ids(all="1")), 3)

    def test_unknown_status_falls_back_to_active(self):
        self.assertEqual(len(self.get_ids(status="xyz")), 2)

    def test_filter_by_seminar_and_participant(self):
        self.assertEqual(
            self.get_ids(seminar=self.python.pk), [self.second.pk]
        )
        self.assertEqual(
            self.get_ids(
                seminar=self.django.pk,
                participant=self.boris.pk,
                status="all",
            ),
            [self.cancelled.pk],
        )

    def test_filter_by_seminar_date(self):
        self.assertEqual(self.get_ids(date="2026-10-12"), [self.second.pk])

    def test_wrong_date_shows_error(self):
        response = self.client.get(
            reverse("registrations:list"), {"date": "abc"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["error"])

    def test_wrong_ids_are_ignored(self):
        self.assertEqual(len(self.get_ids(seminar="abc")), 2)

    def test_search_by_several_fields(self):
        self.assertEqual(
            self.get_ids(q="boris@", status="all"), [self.cancelled.pk]
        )
        self.assertEqual(self.get_ids(q="pyth"), [self.second.pk])
        self.assertEqual(self.get_ids(q="нет такого"), [])

    def test_sorting(self):
        Registration.objects.create(
            seminar=self.python, participant=self.clara
        )
        Registration.objects.create(
            seminar=self.django, participant=self.clara
        )
        response = self.client.get(
            reverse("registrations:list"), {"sort": "participant"}
        )
        names = [
            item["participant_name"]
            for item in response.context["registrations"]
        ]
        self.assertEqual(names, sorted(names))

    def test_unknown_sort_uses_default(self):
        response = self.client.get(
            reverse("registrations:list"), {"sort": "id; DROP"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["sort"], "date")

    def test_pagination_keeps_filters(self):
        for number in range(REGISTRATIONS_PER_PAGE + 2):
            participant = Participant.objects.create(
                name=f"User {number}", email=f"user{number}@example.com"
            )
            Registration.objects.create(
                seminar=self.python, participant=participant
            )
        params = {"seminar": self.python.pk, "sort": "participant"}
        response = self.client.get(reverse("registrations:list"), params)
        page = response.context["page_obj"]
        self.assertEqual(len(page), REGISTRATIONS_PER_PAGE)
        self.assertEqual(page.paginator.num_pages, 2)
        # Ссылка на вторую страницу сохраняет фильтр и сортировку.
        self.assertContains(response, "sort=participant")
        self.assertContains(response, "page=2")

        params["page"] = "2"
        second = self.client.get(reverse("registrations:list"), params)
        self.assertEqual(len(second.context["page_obj"]), 3)

    def test_wrong_page_number_opens_first_page(self):
        response = self.client.get(
            reverse("registrations:list"), {"page": "abc"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].number, 1)


class RegistrationDetailTests(RegistrationTestData):
    """Проверка карточки регистрации."""

    def test_detail_shows_related_objects(self):
        response = self.client.get(
            reverse("registrations:detail", args=[self.first.pk])
        )
        self.assertContains(response, "Anna")
        self.assertContains(response, "Django ORM")
        self.assertContains(response, "21.09.2026")

    def test_missing_registration_returns_404(self):
        response = self.client.get(
            reverse("registrations:detail", args=[9999])
        )
        self.assertEqual(response.status_code, 404)


class StatisticsTests(RegistrationTestData):
    """Проверка показателей на странице статистики."""

    def setUp(self):
        self.response = self.client.get(reverse("registrations:statistics"))

    def test_totals(self):
        totals = self.response.context["totals"]
        self.assertEqual(
            totals, {"total": 3, "active": 2, "cancelled": 1}
        )

    def test_seminar_statistics_ignore_cancelled(self):
        counts = {
            item.title: item.registered_count
            for item in self.response.context["seminar_statistics"]
        }
        self.assertEqual(counts, {"Django ORM": 1, "Python": 1})

    def test_participants_without_registrations_have_zero(self):
        counts = {
            item.name: item.registrations_count
            for item in self.response.context["participant_statistics"]
        }
        self.assertEqual(counts, {"Anna": 2, "Boris": 0, "Clara": 0})

    def test_popular_seminars(self):
        # Django ORM: 1 из 2 мест (половина), Python: 1 из 10.
        titles = [
            item.title for item in self.response.context["popular_seminars"]
        ]
        self.assertEqual(titles, ["Django ORM"])

    def test_idle_participants(self):
        names = [
            item.name for item in self.response.context["idle_participants"]
        ]
        self.assertEqual(names, ["Boris", "Clara"])


class ImportFromSourceDbTests(TestCase):
    """Проверка переноса данных из базы ПР7 в модели Django."""

    def make_source_db(self, directory):
        """Создать во временном каталоге базу со структурой ПР7."""
        source_db = Path(directory) / "source.sqlite"
        init_db(source_db)
        connection = get_connection(source_db)
        connection.executescript(
            """
            INSERT INTO seminars VALUES (7, 'ORM', '2026-09-21', 2);
            INSERT INTO participants VALUES (3, 'Anna', 'a@example.com');
            INSERT INTO registrations VALUES (5, 7, 3, 1);
            INSERT INTO talks VALUES (4, 7, 'Models', 'Anna', '12:15', 10);
            """
        )
        connection.commit()
        connection.close()
        return source_db

    def test_import_keeps_ids_links_and_types(self):
        with tempfile.TemporaryDirectory() as directory:
            source_db = self.make_source_db(directory)
            with redirect_stdout(io.StringIO()):
                import_data(source_db)
                # Повторный запуск не создаёт дубликатов.
                import_data(source_db)

        self.assertEqual(Seminar.objects.count(), 1)
        self.assertEqual(Registration.objects.count(), 1)
        registration = Registration.objects.select_related(
            "seminar", "participant"
        ).get(pk=5)
        self.assertEqual(registration.seminar.pk, 7)
        self.assertEqual(registration.seminar.seminar_date, date(2026, 9, 21))
        self.assertEqual(registration.participant.name, "Anna")
        self.assertTrue(registration.is_cancelled)
        talk = registration.seminar.talks.get()
        self.assertEqual(talk.start_time, time(12, 15))
