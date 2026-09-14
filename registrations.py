"""Функции для работы с регистрацией участников на семинары."""


def is_registration_open(
    registrations: list[dict],
    seminar_id: int,
    max_participants: int,
) -> bool:
    """Проверить, есть ли свободные места для регистрации на семинар."""
    registered_count = sum(
        1 for reg in registrations if reg["seminar_id"] == seminar_id
    )
    return registered_count < max_participants


def create_registration(
    registrations: list[dict],
    seminar_id: int,
    participant_name: str,
) -> dict:
    """Зарегистрировать участника на семинар.

    Повторная регистрация одного и того же участника на один
    и тот же семинар запрещена.
    """
    for reg in registrations:
        if (
            reg["seminar_id"] == seminar_id
            and reg["participant_name"] == participant_name
        ):
            raise ValueError("Участник уже зарегистрирован на этот семинар")

    registration_id = max((r["id"] for r in registrations), default=0) + 1
    registration = {
        "id": registration_id,
        "seminar_id": seminar_id,
        "participant_name": participant_name,
    }
    registrations.append(registration)
    return registration


def cancel_registration(
    registrations: list[dict], registration_id: int
) -> bool:
    """Отменить регистрацию участника по идентификатору."""
    for index, reg in enumerate(registrations):
        if reg["id"] == registration_id:
            del registrations[index]
            return True
    return False


def get_registration_status(current: int, max_count: int) -> str:
    """Вернуть текстовый статус регистрации (функция из ПР1)."""
    free_places = max_count - current
    if free_places > 0:
        return f"Регистрация открыта, свободных мест: {free_places}"
    return "Мест нет, регистрация закрыта"