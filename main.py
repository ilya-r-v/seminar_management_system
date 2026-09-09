from datetime import date

seminar_title = "Введение в машинное обучение"
seminar_date = date(2026, 10, 12)
max_participants = 25
current_participants = 23

talk_title = "Основы нейронных сетей"
speaker_name = "Роднов И.В."
talk_duration_minutes = 40


def get_registration_status(current, max_count):
    """Определяет, можно ли ещё зарегистрироваться на семинар."""
    free_places = max_count - current
    if free_places > 0:
        return f"Регистрация открыта, свободных мест: {free_places}"
    return "Мест нет, регистрация закрыта"


def get_talk_summary(title, speaker, duration):
    """Формирует краткое описание доклада для расписания."""
    hours = duration // 60
    minutes = duration % 60
    if hours > 0:
        duration_str = f"{hours} ч {minutes} мин"
    else:
        duration_str = f"{minutes} мин"
    return f"Доклад «{title}» ({speaker}), длительность: {duration_str}"


registration_status = get_registration_status(current_participants, max_participants)
talk_summary = get_talk_summary(talk_title, speaker_name, talk_duration_minutes)

print(f"Семинар: {seminar_title}")
print(f"Дата проведения: {seminar_date}")
print(f"Зарегистрировано участников: {current_participants} из {max_participants}")
print(registration_status)
print("-" * 40)
print(talk_summary)