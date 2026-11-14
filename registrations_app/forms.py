"""Формы приложения «Регистрации»."""

from django import forms
from django.utils import timezone

from participants_app.models import Participant
from registrations_app.models import Registration
from seminars_app.models import Seminar

# Значение фильтра «все статусы»: его нет среди статусов модели.
ALL_STATUSES = "all"


class RegistrationFilterForm(forms.Form):
    """Форма фильтрации списка регистраций (GET-параметры).

    Форма ничего не сохраняет: она только проверяет параметры
    из адресной строки и превращает их в значения нужных типов.
    Все поля необязательные — пустое поле означает «без условия».
    """

    q = forms.CharField(
        required=False,
        max_length=200,
        label="Поиск",
        help_text="Имя или почта участника, название семинара.",
        widget=forms.TextInput(
            attrs={"type": "search", "class": "form-control"}
        ),
    )
    # ModelChoiceField проверяет, что выбранный объект существует.
    seminar = forms.ModelChoiceField(
        queryset=Seminar.objects.order_by("title"),
        required=False,
        label="Семинар",
        empty_label="Все семинары",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    participant = forms.ModelChoiceField(
        queryset=Participant.objects.order_by("name"),
        required=False,
        label="Участник",
        empty_label="Все участники",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    # DateField превращает строку из адреса в объект date.
    date = forms.DateField(
        required=False,
        label="Дата семинара",
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
    )
    # ChoiceField пропускает только значения из списка choices.
    status = forms.ChoiceField(
        required=False,
        label="Статус",
        choices=[
            (Registration.Status.ACTIVE.value, "Активные"),
            (Registration.Status.CANCELLED.value, "Отменённые"),
            (Registration.Status.COMPLETED.value, "Завершённые"),
            (ALL_STATUSES, "Все"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    sort = forms.ChoiceField(
        required=False,
        label="Сортировать по",
        choices=[
            ("date", "Дате семинара"),
            ("seminar", "Семинару"),
            ("participant", "Участнику"),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
    )


class RegistrationForm(forms.ModelForm):
    """Форма создания и редактирования регистрации."""

    class Meta:
        # Модель, из которой Django берёт поля и их типы.
        model = Registration
        # Поле status в форму не входит: статус новой регистрации
        # задаёт приложение («активна»), а меняется он отдельной
        # операцией отмены. Так пользователь не может подставить
        # произвольный статус.
        fields = ["seminar", "participant"]
        labels = {
            "seminar": "Семинар",
            "participant": "Участник",
        }
        help_texts = {
            "seminar": "Выберите семинар, на который есть места.",
            "participant": (
                "Новых участников добавляет администратор "
                "в административной панели."
            ),
        }
        widgets = {
            "seminar": forms.Select(attrs={"class": "form-select"}),
            "participant": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Порядок и подписи пустых вариантов в списках выбора.
        self.fields["seminar"].queryset = Seminar.objects.order_by(
            "seminar_date", "title"
        )
        self.fields["seminar"].empty_label = "Выберите семинар"
        self.fields["participant"].queryset = (
            Participant.objects.order_by("name")
        )
        self.fields["participant"].empty_label = "Выберите участника"

    def clean_seminar(self):
        """Запретить регистрацию на семинар, который уже прошёл."""
        seminar = self.cleaned_data["seminar"]
        # Текущая дата с учётом часового пояса проекта.
        today = timezone.localdate()
        # При редактировании семинар можно оставить прежним,
        # даже если он уже прошёл: проверяется только новый выбор.
        seminar_changed = seminar.pk != self.instance.seminar_id
        if seminar_changed and seminar.seminar_date < today:
            raise forms.ValidationError(
                "Нельзя зарегистрироваться на семинар, "
                "который уже прошёл."
            )
        return seminar

    def clean(self):
        """Проверка двух полей вместе: запрет повторной регистрации."""
        cleaned_data = super().clean()
        seminar = cleaned_data.get("seminar")
        participant = cleaned_data.get("participant")

        # Проверяем только если оба поля прошли свою валидацию.
        if seminar and participant:
            # Активные регистрации этого участника на этот семинар.
            # При редактировании сама запись из проверки исключается.
            duplicates = Registration.objects.active().filter(
                seminar=seminar,
                participant=participant,
            ).exclude(pk=self.instance.pk)
            if duplicates.exists():
                # Ошибка относится ко всей форме, а не к одному полю.
                raise forms.ValidationError(
                    "Этот участник уже зарегистрирован на выбранный "
                    "семинар."
                )
        return cleaned_data
