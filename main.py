"""Точка запуска приложения «Система управления семинарами»."""
from typing import List, Optional

from models import Participant, Registration, Seminar, Talk
from models.participants import (
    add_participant,
    find_participant_by_email,
    show_participants,
)
from models.registrations import (
    cancel_registration,
    create_registration,
    get_registration_status,
    show_registrations,
)
from models.seminars import (
    add_seminar,
    find_seminar,
    find_seminar_by_id,
    show_seminars,
)
from models.talks import add_talk, show_schedule
from storage import (
    load_participants,
    load_registrations,
    load_seminars,
    load_talks,
    save_participants,
    save_registrations,
    save_seminars,
    save_talks,
)
from utils import input_date, input_int

SEMINARS_FILE = "data/seminars.json"
PARTICIPANTS_FILE = "data/participants.json"
REGISTRATIONS_FILE = "data/registrations.json"
TALKS_FILE = "data/talks.json"


def choose_seminar(seminars: List[Seminar]) -> Optional[Seminar]:
    """Запросить у пользователя идентификатор семинара и найти его."""
    seminar_id = input_int("Идентификатор семинара: ")
    seminar = find_seminar_by_id(seminars, seminar_id)
    if seminar is None:
        print("Семинар не найден")
    return seminar


def register_participant(
    registrations: List[Registration],
    participants: List[Participant],
    seminar: Seminar,
) -> None:
    """Сценарий регистрации участника на выбранный семинар."""
    registered_count = sum(
        1 for reg in registrations
        if reg.seminar.id == seminar.id and not reg.is_cancelled
    )
    print(
        get_registration_status(registered_count, seminar.max_participants)
    )
    if not seminar.is_available_for(registered_count):
        return

    email = input("Email участника: ")
    participant = find_participant_by_email(participants, email)
    if participant is None:
        name = input("Имя участника: ")
        participant = add_participant(participants, name, email)
        save_participants(PARTICIPANTS_FILE, participants)

    try:
        registration = create_registration(
            registrations, seminar, participant
        )
    except ValueError as error:
        print(f"Ошибка: {error}")
        return

    if registration is None:
        print("Мест нет, регистрация закрыта")
        return

    save_registrations(REGISTRATIONS_FILE, registrations)
    print("Регистрация выполнена")


def add_talk_to_seminar(talks: List[Talk], seminar: Seminar) -> None:
    """Сценарий добавления доклада в программу семинара."""
    title = input("Название доклада: ")
    speaker = input("Докладчик: ")
    start_time = input("Время начала (ЧЧ:ММ): ")
    duration = input_int("Длительность (мин): ")
    add_talk(talks, seminar, title, speaker, start_time, duration)
    save_talks(TALKS_FILE, talks)
    print("Доклад добавлен")


def main() -> None:
    """Точка запуска приложения: меню и вызов функций проекта."""
    seminars = load_seminars(SEMINARS_FILE)
    participants = load_participants(PARTICIPANTS_FILE)
    registrations = load_registrations(
        REGISTRATIONS_FILE, seminars, participants
    )
    talks = load_talks(TALKS_FILE, seminars)

    menu = (
        "\n=== Система управления семинарами ===\n"
        "1. Показать семинары\n"
        "2. Добавить семинар\n"
        "3. Найти семинар по названию\n"
        "4. Зарегистрироваться на семинар\n"
        "5. Отменить регистрацию\n"
        "6. Показать участников\n"
        "7. Показать регистрации\n"
        "8. Добавить доклад\n"
        "9. Показать расписание семинара\n"
        "0. Выход"
    )

    while True:
        print(menu)
        choice = input("Выберите действие: ")

        if choice == "1":
            show_seminars(seminars)

        elif choice == "2":
            title = input("Название семинара: ")
            seminar_date = input_date("Дата (ДД.ММ.ГГГГ): ")
            max_participants = input_int("Максимум участников: ")
            add_seminar(seminars, title, seminar_date, max_participants)
            save_seminars(SEMINARS_FILE, seminars)
            print("Семинар добавлен")

        elif choice == "3":
            query = input("Подстрока названия: ")
            found = find_seminar(seminars, query)
            if found:
                for found_seminar in found:
                    print(f"{found_seminar.id}. {found_seminar}")
            else:
                print("Ничего не найдено")

        elif choice == "4":
            seminar = choose_seminar(seminars)
            if seminar is not None:
                register_participant(registrations, participants, seminar)

        elif choice == "5":
            registration_id = input_int("Идентификатор регистрации: ")
            if cancel_registration(registrations, registration_id):
                save_registrations(REGISTRATIONS_FILE, registrations)
                print("Регистрация отменена")
            else:
                print("Регистрация не найдена")

        elif choice == "6":
            show_participants(participants)

        elif choice == "7":
            show_registrations(registrations)

        elif choice == "8":
            seminar = choose_seminar(seminars)
            if seminar is not None:
                add_talk_to_seminar(talks, seminar)

        elif choice == "9":
            seminar = choose_seminar(seminars)
            if seminar is not None:
                show_schedule(talks, seminar)

        elif choice == "0":
            print("До встречи!")
            break

        else:
            print("Неизвестный пункт меню")


if __name__ == "__main__":
    main()
