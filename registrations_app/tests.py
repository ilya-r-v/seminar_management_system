"""Тесты приложения «Регистрации»: модель, список и статистика."""

import io
import tempfile
from contextlib import redirect_stdout
from datetime import date, time, timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import connection
from django.db.models import ProtectedError
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from db.database import get_connection, init_db
from db.import_sqlite_to_orm import import_data
from participants_app.models import Participant
from registrations_app.models import Registration
from registrations_app.forms import RegistrationForm
from registrations_app.views import NO_PLACES_ERROR, REGISTRATIONS_PER_PAGE
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

    def test_unknown_status_is_rejected_by_form(self):
        response = self.client.get(
            reverse("registrations:list"), {"status": "xyz"}
        )
        self.assertEqual(response.status_code, 200)
        # Значения нет в choices: ошибка поля и общее сообщение,
        # список показывается с условиями по умолчанию.
        self.assertIn("status", response.context["form"].errors)
        self.assertEqual(response.context["status"], "active")
        self.assertEqual(len(response.context["registrations"]), 2)
        self.assertContains(response, "Проверьте введённые значения")

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
        self.assertIn("date", response.context["form"].errors)

    def test_missing_seminar_is_rejected_by_form(self):
        for value in ("abc", "999999"):
            with self.subTest(value=value):
                response = self.client.get(
                    reverse("registrations:list"), {"seminar": value}
                )
                self.assertEqual(response.status_code, 200)
                self.assertIn("seminar", response.context["form"].errors)
                # Непроверенное значение к запросу не применяется.
                self.assertEqual(len(response.context["registrations"]), 2)

    def test_form_keeps_selected_values(self):
        response = self.client.get(
            reverse("registrations:list"),
            {"seminar": self.python.pk, "sort": "participant", "q": "ann"},
        )
        form = response.context["form"]
        self.assertTrue(form.is_bound)
        self.assertEqual(form.cleaned_data["seminar"], self.python)
        self.assertContains(response, 'value="ann"')

    def test_empty_request_gives_unbound_form(self):
        response = self.client.get(reverse("registrations:list"))
        self.assertFalse(response.context["form"].is_bound)
        self.assertIsNone(response.context["error"])

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
        self.assertIn("sort", response.context["form"].errors)

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


class RegistrationFormTestData(TestCase):
    """Данные для проверки форм: семинары в будущем и в прошлом."""

    @classmethod
    def setUpTestData(cls):
        today = timezone.localdate()
        cls.future = Seminar.objects.create(
            title="Future",
            seminar_date=today + timedelta(days=10),
            max_participants=2,
        )
        cls.today_seminar = Seminar.objects.create(
            title="Today",
            seminar_date=today,
            max_participants=1,
        )
        cls.past = Seminar.objects.create(
            title="Past",
            seminar_date=today - timedelta(days=1),
            max_participants=5,
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

    def post_create(self, seminar, participant, **extra):
        data = {"seminar": seminar.pk, "participant": participant.pk}
        data.update(extra)
        return self.client.post(reverse("registrations:create"), data)

    def post_update(self, registration, seminar, participant):
        return self.client.post(
            reverse("registrations:update", args=[registration.pk]),
            {"seminar": seminar.pk, "participant": participant.pk},
        )


class RegistrationFormTests(RegistrationFormTestData):
    """Проверка самой формы RegistrationForm."""

    def test_form_has_only_allowed_fields(self):
        self.assertEqual(
            list(RegistrationForm().fields), ["seminar", "participant"]
        )

    def test_valid_data(self):
        form = RegistrationForm(
            {"seminar": self.future.pk, "participant": self.anna.pk}
        )
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        form = RegistrationForm({})
        self.assertFalse(form.is_valid())
        self.assertEqual(set(form.errors), {"seminar", "participant"})

    def test_past_seminar_is_field_error(self):
        form = RegistrationForm(
            {"seminar": self.past.pk, "participant": self.anna.pk}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("уже прошёл", form.errors["seminar"][0])

    def test_today_seminar_is_allowed(self):
        form = RegistrationForm(
            {"seminar": self.today_seminar.pk, "participant": self.anna.pk}
        )
        self.assertTrue(form.is_valid())

    def test_duplicate_is_non_field_error(self):
        Registration.objects.create(
            seminar=self.future, participant=self.anna
        )
        form = RegistrationForm(
            {"seminar": self.future.pk, "participant": self.anna.pk}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("уже зарегистрирован", form.non_field_errors()[0])

    def test_cancelled_registration_is_not_duplicate(self):
        Registration.objects.create(
            seminar=self.future,
            participant=self.anna,
            status=Registration.Status.CANCELLED,
        )
        form = RegistrationForm(
            {"seminar": self.future.pk, "participant": self.anna.pk}
        )
        self.assertTrue(form.is_valid())


class RegistrationCreateTests(RegistrationFormTestData):
    """Создание регистрации через форму."""

    def test_get_shows_empty_form(self):
        response = self.client.get(reverse("registrations:create"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["form"].is_bound)
        self.assertContains(response, "csrfmiddlewaretoken")
        # Подсказка из help_texts.
        self.assertContains(response, "на который есть места")

    def test_initial_seminar_from_address(self):
        response = self.client.get(
            reverse("registrations:create"), {"seminar": self.future.pk}
        )
        self.assertEqual(
            response.context["form"].initial["seminar"], self.future.pk
        )

    def test_wrong_initial_seminar_is_ignored(self):
        response = self.client.get(
            reverse("registrations:create"), {"seminar": "abc"}
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_post_creates_active_registration(self):
        response = self.post_create(self.future, self.anna)
        registration = Registration.objects.get()
        self.assertRedirects(
            response,
            reverse("registrations:detail", args=[registration.pk]),
        )
        self.assertEqual(registration.seminar, self.future)
        self.assertEqual(registration.participant, self.anna)
        self.assertEqual(registration.status, Registration.Status.ACTIVE)

    def test_status_from_request_is_ignored(self):
        self.post_create(self.future, self.anna, status="completed")
        self.assertEqual(
            Registration.objects.get().status, Registration.Status.ACTIVE
        )

    def test_empty_post_shows_errors_and_saves_nothing(self):
        response = self.client.post(reverse("registrations:create"), {})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Обязательное поле")
        self.assertEqual(Registration.objects.count(), 0)

    def test_past_seminar_is_rejected(self):
        response = self.post_create(self.past, self.anna)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "уже прошёл")
        self.assertEqual(Registration.objects.count(), 0)

    def test_full_seminar_is_rejected(self):
        Registration.objects.create(
            seminar=self.today_seminar, participant=self.anna
        )
        response = self.post_create(self.today_seminar, self.boris)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context["form"].non_field_errors(), [NO_PLACES_ERROR]
        )
        self.assertContains(response, NO_PLACES_ERROR)
        # Введённые значения сохраняются в форме.
        self.assertEqual(
            response.context["form"]["participant"].value(),
            str(self.boris.pk),
        )
        self.assertEqual(Registration.objects.count(), 1)

    def test_cancelled_registration_does_not_take_place(self):
        Registration.objects.create(
            seminar=self.today_seminar,
            participant=self.anna,
            status=Registration.Status.CANCELLED,
        )
        self.post_create(self.today_seminar, self.boris)
        self.assertEqual(Registration.objects.active().count(), 1)

    def test_duplicate_is_rejected(self):
        self.post_create(self.future, self.anna)
        response = self.post_create(self.future, self.anna)
        self.assertContains(response, "уже зарегистрирован")
        self.assertEqual(Registration.objects.count(), 1)

    def test_missing_seminar_is_rejected(self):
        response = self.client.post(
            reverse("registrations:create"),
            {"seminar": 999999, "participant": self.anna.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("seminar", response.context["form"].errors)

    def test_post_without_csrf_token_is_forbidden(self):
        client = Client(enforce_csrf_checks=True)
        response = client.post(
            reverse("registrations:create"),
            {"seminar": self.future.pk, "participant": self.anna.pk},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Registration.objects.count(), 0)

    def test_new_registration_appears_in_list(self):
        self.post_create(self.future, self.anna)
        response = self.client.get(reverse("registrations:list"))
        self.assertContains(response, "Anna")
        self.assertContains(response, "Редактировать")
        self.assertContains(response, "Отменить")


class RegistrationUpdateTests(RegistrationFormTestData):
    """Редактирование регистрации через форму."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.registration = Registration.objects.create(
            seminar=cls.future, participant=cls.anna
        )

    def test_get_shows_current_values(self):
        response = self.client.get(
            reverse("registrations:update", args=[self.registration.pk])
        )
        self.assertEqual(response.status_code, 200)
        form = response.context["form"]
        self.assertEqual(form.instance, self.registration)
        self.assertEqual(form["seminar"].value(), self.future.pk)
        self.assertContains(response, "Сохранить изменения")

    def test_save_without_changes_does_not_conflict_with_itself(self):
        response = self.post_update(
            self.registration, self.future, self.anna
        )
        self.assertEqual(response.status_code, 302)
        # Новая запись не появилась.
        self.assertEqual(Registration.objects.count(), 1)

    def test_last_place_is_not_blocked_by_itself(self):
        registration = Registration.objects.create(
            seminar=self.today_seminar, participant=self.boris
        )
        response = self.post_update(
            registration, self.today_seminar, self.clara
        )
        self.assertEqual(response.status_code, 302)
        registration.refresh_from_db()
        self.assertEqual(registration.participant, self.clara)

    def test_change_participant(self):
        self.post_update(self.registration, self.future, self.boris)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.participant, self.boris)
        self.assertEqual(Registration.objects.count(), 1)

    def test_change_to_full_seminar_is_rejected(self):
        Registration.objects.create(
            seminar=self.today_seminar, participant=self.boris
        )
        response = self.post_update(
            self.registration, self.today_seminar, self.anna
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, NO_PLACES_ERROR)
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.seminar, self.future)

    def test_change_to_past_seminar_is_rejected(self):
        response = self.post_update(self.registration, self.past, self.anna)
        self.assertContains(response, "уже прошёл")
        self.registration.refresh_from_db()
        self.assertEqual(self.registration.seminar, self.future)

    def test_past_seminar_can_stay_unchanged(self):
        registration = Registration.objects.create(
            seminar=self.past, participant=self.boris
        )
        response = self.post_update(registration, self.past, self.clara)
        self.assertEqual(response.status_code, 302)

    def test_change_to_duplicate_is_rejected(self):
        Registration.objects.create(
            seminar=self.future, participant=self.boris
        )
        response = self.post_update(
            self.registration, self.future, self.boris
        )
        self.assertContains(response, "уже зарегистрирован")

    def test_status_is_kept(self):
        self.post_update(self.registration, self.future, self.boris)
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status, Registration.Status.ACTIVE
        )

    def test_missing_registration_returns_404(self):
        response = self.client.get(
            reverse("registrations:update", args=[999999])
        )
        self.assertEqual(response.status_code, 404)

    def test_cancelled_registration_cannot_be_edited(self):
        self.registration.cancel()
        response = self.client.get(
            reverse("registrations:update", args=[self.registration.pk])
        )
        self.assertEqual(response.status_code, 404)


class RegistrationCancelTests(RegistrationFormTestData):
    """Отмена регистрации POST-запросом."""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.registration = Registration.objects.create(
            seminar=cls.today_seminar, participant=cls.anna
        )
        cls.address = reverse(
            "registrations:cancel", args=[cls.registration.pk]
        )

    def test_post_cancels_but_keeps_record(self):
        response = self.client.post(self.address)
        self.assertRedirects(response, reverse("registrations:list"))
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status, Registration.Status.CANCELLED
        )
        self.assertEqual(Registration.objects.count(), 1)

    def test_get_is_not_allowed(self):
        response = self.client.get(self.address)
        self.assertEqual(response.status_code, 405)
        self.registration.refresh_from_db()
        self.assertEqual(
            self.registration.status, Registration.Status.ACTIVE
        )

    def test_second_cancel_returns_404(self):
        self.client.post(self.address)
        self.assertEqual(self.client.post(self.address).status_code, 404)

    def test_missing_registration_returns_404(self):
        response = self.client.post(
            reverse("registrations:cancel", args=[999999])
        )
        self.assertEqual(response.status_code, 404)

    def test_cancel_without_csrf_token_is_forbidden(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(self.address).status_code, 403)

    def test_cancelled_is_hidden_from_active_list(self):
        self.client.post(self.address)
        response = self.client.get(reverse("registrations:list"))
        self.assertEqual(len(response.context["registrations"]), 0)

    def test_cancel_frees_place(self):
        # Единственное место занято: новая регистрация невозможна.
        self.post_create(self.today_seminar, self.boris)
        self.assertEqual(Registration.objects.active().count(), 1)
        # После отмены место освобождается.
        self.client.post(self.address)
        self.post_create(self.today_seminar, self.boris)
        active = Registration.objects.active().get()
        self.assertEqual(active.participant, self.boris)

    def test_buttons_only_for_active_registrations(self):
        detail = reverse(
            "registrations:detail", args=[self.registration.pk]
        )
        self.assertContains(self.client.get(detail), self.address)
        self.client.post(self.address)
        self.assertNotContains(self.client.get(detail), self.address)
