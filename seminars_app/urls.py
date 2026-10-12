"""Маршруты страниц семинаров."""

from django.urls import path

from seminars_app import views

app_name = "seminars"

urlpatterns = [
    path("", views.seminar_list, name="list"),
    path("<int:seminar_id>/", views.seminar_detail, name="detail"),
]
