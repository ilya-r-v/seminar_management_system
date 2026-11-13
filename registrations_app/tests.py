"""Тесты приложения «Регистрации»: модель, список и статистика."""

import io
import tempfile
from contextlib import redirect_stdout
from datetime import date, time
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import ProtectedError
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
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
            seminar=cls.django,
            participant=cls.boris,
            status=Registration.Status.CANCELLED,
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
        self.assertEqual(self.first.status, Registration.Status.CANCELLED)

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
            totals,
            {"total": 3, "active": 2, "cancelled": 1, "completed": 0},
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
        self.assertEqual(
            registration.status, Registration.Status.CANCELLED
        )
        talk = registration.seminar.talks.get()
        self.assertEqual(talk.start_time, time(12, 15))


class RegistrationManagerTests(RegistrationTestData):
    """Проверка методов менеджера регистраций."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.completed = Registration.objects.create(
            seminar=cls.python,
            participant=cls.clara,
            status=Registration.Status.COMPLETED,
        )

    def test_all_returns_every_status(self):
        self.assertEqual(Registration.objects.count(), 4)

    def test_status_methods(self):
        self.assertEqual(
            list(Registration.objects.active()), [self.first, self.second]
        )
        self.assertEqual(
            list(Registration.objects.cancelled()), [self.cancelled]
        )
        self.assertEqual(
            list(Registration.objects.completed()), [self.completed]
        )

    def test_methods_can_be_combined(self):
        registrations = Registration.objects.active().for_date(
            date(2026, 10, 12)
        )
        self.assertEqual(list(registrations), [self.second])

    def test_new_registration_is_active(self):
        registration = Registration.objects.create(
            seminar=self.django, participant=self.clara
        )
        self.assertEqual(registration.status, Registration.Status.ACTIVE)
        self.assertEqual(registration.get_status_display(), "Активна")

    def test_list_filter_by_completed(self):
        self.assertEqual(
            self.get_ids(status="completed"), [self.completed.pk]
        )
        self.assertEqual(len(self.get_ids(status="all")), 4)
        # Завершённые регистрации в списке активных не показываются.
        self.assertNotIn(self.completed.pk, self.get_ids())

    def test_statistics_count_every_status(self):
        response = self.client.get(reverse("registrations:statistics"))
        self.assertEqual(
            response.context["totals"],
            {"total": 4, "active": 2, "cancelled": 1, "completed": 1},
        )
        # У Клары только завершённая регистрация: активных у неё нет.
        names = [
            item.name for item in response.context["idle_participants"]
        ]
        self.assertEqual(names, ["Boris", "Clara"])

    def test_status_is_shown_in_list(self):
        response = self.client.get(
            reverse("registrations:list"), {"status": "all"}
        )
        self.assertContains(response, "Активна")
        self.assertContains(response, "Отменена")
        self.assertContains(response, "Завершена")


class RegistrationQueryCountTests(RegistrationTestData):
    """Число SQL-запросов не растёт вместе с числом записей."""

    def test_list_queries(self):
        for number in range(12):
            participant = Participant.objects.create(
                name=f"User {number}", email=f"user{number}@example.com"
            )
            Registration.objects.create(
                seminar=self.python, participant=participant
            )
        # 1 — подсчёт записей для страниц, 2 — записи страницы,
        # 3 и 4 — списки семинаров и участников для формы,
        # 5 — число семинаров в навигации (контекстный процессор).
        with self.assertNumQueries(5):
            self.client.get(reverse("registrations:list"))

    def test_detail_queries(self):
        # 1 — регистрация вместе с семинаром и участником
        # (select_related), 2 — число семинаров в навигации.
        with self.assertNumQueries(2):
            self.client.get(
                reverse("registrations:detail", args=[self.first.pk])
            )


class AdminTests(RegistrationTestData):
    """Проверка административной панели."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.admin_user = get_user_model().objects.create_superuser(
            username="admin", password="admin-password"
        )

    def setUp(self):
        self.client.force_login(self.admin_user)

    def test_admin_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_index_shows_russian_names(self):
        response = self.client.get(reverse("admin:index"))
        for name in ("Семинары", "Участники", "Регистрации", "Доклады"):
            self.assertContains(response, name)

    def test_lists_open(self):
        names = [
            "admin:seminars_app_seminar_changelist",
            "admin:seminars_app_talk_changelist",
            "admin:participants_app_participant_changelist",
            "admin:registrations_app_registration_changelist",
        ]
        for name in names:
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, 200)

    def test_seminar_list_shows_active_registrations(self):
        response = self.client.get(
            reverse("admin:seminars_app_seminar_changelist")
        )
        self.assertContains(response, "Активных регистраций")
        # Ссылка на страницу семинара на сайте.
        self.assertContains(response, self.django.get_absolute_url())

    def test_seminar_card_shows_inlines_and_site_link(self):
        response = self.client.get(
            reverse(
                "admin:seminars_app_seminar_change", args=[self.django.pk]
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Регистрации")
        self.assertContains(response, "Доклады")
        self.assertContains(response, "Смотреть на сайте")
        # Подсказка к полю из help_text.
        self.assertContains(response, "сколько человек может")

    def test_participant_card_opens(self):
        response = self.client.get(
            reverse(
                "admin:participants_app_participant_change",
                args=[self.anna.pk],
            )
        )
        self.assertEqual(response.status_code, 200)

    def test_registration_search_by_related_fields(self):
        address = reverse("admin:registrations_app_registration_changelist")
        response = self.client.get(address, {"q": "boris@"})
        self.assertEqual(response.context["cl"].result_count, 1)
        response = self.client.get(address, {"q": "Python"})
        self.assertEqual(response.context["cl"].result_count, 1)

    def test_registration_filter_by_status(self):
        address = reverse("admin:registrations_app_registration_changelist")
        response = self.client.get(address, {"status__exact": "cancelled"})
        self.assertEqual(response.context["cl"].result_count, 1)

    def test_registration_list_has_no_extra_queries(self):
        address = reverse("admin:registrations_app_registration_changelist")
        self.client.get(address)
        with CaptureQueriesContext(connection) as before:
            self.client.get(address)
        for number in range(10):
            participant = Participant.objects.create(
                name=f"User {number}", email=f"user{number}@example.com"
            )
            Registration.objects.create(
                seminar=self.python, participant=participant
            )
        with CaptureQueriesContext(connection) as after:
            self.client.get(address)
        # list_select_related: число запросов не зависит от числа строк.
        self.assertEqual(len(before), len(after))

    def run_action(self, action, registrations):
        return self.client.post(
            reverse("admin:registrations_app_registration_changelist"),
            {
                "action": action,
                "_selected_action": [item.pk for item in registrations],
            },
            follow=True,
        )

    def test_cancel_action(self):
        response = self.run_action(
            "cancel_registrations", [self.first, self.second]
        )
        self.assertContains(response, "Отменено регистраций: 2.")
        self.assertEqual(Registration.objects.active().count(), 0)

    def test_restore_action(self):
        response = self.run_action("restore_registrations", [self.cancelled])
        self.assertContains(response, "Возвращено регистраций: 1.")
        self.assertEqual(Registration.objects.cancelled().count(), 0)
