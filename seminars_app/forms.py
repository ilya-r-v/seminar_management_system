"""Формы приложения «Семинары»."""

from django import forms
from django.utils import timezone

from seminars_app.models import Seminar


class SeminarSearchForm(forms.Form):
    """Форма поиска семинаров по названию (GET-параметр q)."""

    q = forms.CharField(
        # Поиск можно не заполнять: тогда показываются все семинары.
        required=False,
        max_length=200,
        label="Поиск по названию",
        widget=forms.TextInput(
            attrs={
                "type": "search",
                "class": "form-control",
                "placeholder": "Название семинара",
            }
        ),
    )


class AvailableSeminarsForm(forms.Form):
    """Форма поиска семинаров со свободными местами по дате."""

    date = forms.DateField(
        label="Дата",
        help_text="Будут показаны семинары в этот день и позже.",
        # Браузер отобразит элемент выбора даты.
        widget=forms.DateInput(
            attrs={"type": "date", "class": "form-control"}
        ),
        error_messages={
            "required": "Укажите дату.",
            "invalid": "Укажите дату в формате ГГГГ-ММ-ДД.",
        },
    )


class SeminarForm(forms.ModelForm):
    """Форма создания и редактирования семинара (с изображением)."""

    class Meta:
        # Модель, из которой Django берёт поля и их типы.
        model = Seminar
        # Только поля, которыми может управлять пользователь.
        # slug и is_large в форму не входят: slug создаётся
        # автоматически, is_large вычисляет база данных.
        fields = ["title", "seminar_date", "max_participants", "image"]
        labels = {
            "title": "Название",
            "seminar_date": "Дата проведения",
            "max_participants": "Число мест",
            "image": "Изображение",
        }
        help_texts = {
            "title": "Короткое название семинара.",
            "seminar_date": "Семинар нельзя назначить на прошедшую дату.",
        }
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "seminar_date": forms.DateInput(
                # Формат нужен, чтобы при редактировании браузер
                # показал в поле уже сохранённую дату.
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
            "max_participants": forms.NumberInput(
                attrs={"class": "form-control", "min": 1}
            ),
            "image": forms.ClearableFileInput(
                attrs={"class": "form-control", "accept": "image/*"}
            ),
        }

    def clean_seminar_date(self):
        """Запретить назначать семинар на прошедшую дату."""
        seminar_date = self.cleaned_data["seminar_date"]
        # Текущая дата с учётом часового пояса проекта.
        today = timezone.localdate()
        # При редактировании дату уже прошедшего семинара можно
        # оставить прежней: проверяется только изменённая дата.
        date_changed = seminar_date != self.instance.seminar_date
        if date_changed and seminar_date < today:
            raise forms.ValidationError(
                "Нельзя назначить семинар на прошедшую дату."
            )
        return seminar_date
