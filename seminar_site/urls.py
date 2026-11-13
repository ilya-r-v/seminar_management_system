"""Корневая конфигурация маршрутов проекта."""

from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.views import serve as serve_static
from django.urls import include, path, re_path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("homepage.urls")),
    path("seminars/", include("seminars_app.urls")),
    path("registrations/", include("registrations_app.urls")),
    re_path(r"^static/(?P<path>.*)$", serve_static, {"insecure": True}),
]

# Маршруты панели отладки подключаются только при разработке.
if settings.DEBUG and not settings.TESTING:
    urlpatterns += [
        path("__debug__/", include("debug_toolbar.urls")),
    ]

handler404 = "homepage.views.page_not_found"
