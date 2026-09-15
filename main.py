"""Точка запуска приложения «Система управления семинарами»."""
from seminars import add_seminar, find_seminar, sort_seminars
from registrations import (
    create_registration,
    is_registration_open,
    get_registration_status,
)
from talks import add_talk, get_schedule
from storage import (
    load_seminars,
    save_seminars,
    load_registrations,
    save_registrations,
    load_talks,
    save_talks,
)
from utils import input_int, input_date

SEMINARS_FILE = "data/seminars.json"
REGISTRATIONS_FILE = "data/registrations.json"
TALKS_FILE = "data/talks.json"


def show_seminars(seminars: dict[int, dict]) -> None:
    """Вывести список семинаров."""
    if not seminars:
        print("Семинаров пока нет")
        return
    for seminar_id, data in sort_seminars(seminars):
        print(
            f"{seminar_id}. {data['title']} — {data['date']} "
            f"(мест: {data['max_participants']})"
        )


def show_schedule(talks: list[dict], seminar_id: int) -> None:
    """Вывести расписание докладов семинара."""
    schedule = get_schedule(talks, seminar_id)
    if not schedule:
        print("Доклады пока не добавлены")
        return
    for talk in schedule:
        print(
            f"{talk['start_time']} — {talk['title']} ({talk['speaker']}, "
            f"{talk['duration_minutes']} мин)"
        )


def main() -> None:
    """Точка запуска приложения: меню и вызов функций проекта."""
    seminars = load_seminars(SEMINARS_FILE)
    registrations = load_registrations(REGISTRATIONS_FILE)
    talks = load_talks(TALKS_FILE)

    menu = (
        "\n=== Система управления семинарами ===\n"
        "1. Показать семинары\n"
        "2. Добавить семинар\n"
        "3. Найти семинар по названию\n"
        "4. Зарегистрироваться на семинар\n"
        "5. Добавить доклад\n"
        "6. Показать расписание семинара\n"
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
                for seminar_id in found:
                    print(f"{seminar_id}. {seminars[seminar_id]['title']}")
            else:
                print("Ничего не найдено")

        elif choice == "4":
            seminar_id = input_int("Идентификатор семинара: ")
            if seminar_id not in seminars:
                print("Семинар не найден")
                continue
            max_participants = seminars[seminar_id]["max_participants"]
            registered_count = sum(
                1 for reg in registrations if reg["seminar_id"] == seminar_id
            )
            print(get_registration_status(registered_count, max_participants))
            registration_open = is_registration_open(
                registrations, seminar_id, max_participants
            )
            if registration_open:
                participant_name = input("Имя участника: ")
                try:
                    create_registration(
                        registrations, seminar_id, participant_name
                    )
                    save_registrations(REGISTRATIONS_FILE, registrations)
                    print("Регистрация выполнена")
                except ValueError as error:
                    print(f"Ошибка: {error}")

        elif choice == "5":
            seminar_id = input_int("Идентификатор семинара: ")
            if seminar_id not in seminars:
                print("Семинар не найден")
                continue
            title = input("Название доклада: ")
            speaker = input("Докладчик: ")
            start_time = input("Время начала (ЧЧ:ММ): ")
            duration = input_int("Длительность (мин): ")
            add_talk(talks, seminar_id, title, speaker, start_time, duration)
            save_talks(TALKS_FILE, talks)
            print("Доклад добавлен")

        elif choice == "6":
            seminar_id = input_int("Идентификатор семинара: ")
            show_schedule(talks, seminar_id)

        elif choice == "0":
            print("До встречи!")
            break

        else:
            print("Неизвестный пункт меню")


if __name__ == "__main__":
    main()
