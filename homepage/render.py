"""Общая вспомогательная функция для сборки HTML-страниц сайта.
"""

NAV_LINKS = [
    ("/", "Главная"),
    ("/seminars/", "Семинары"),
    ("/registrations/", "Регистрации"),
]


def page(title: str, content: str) -> str:
    """Обернуть содержимое страницы в общий HTML-каркас с Bootstrap."""
    nav_items = "".join(
        f'<li class="nav-item">'
        f'<a class="nav-link" href="{url}">{label}</a></li>'
        for url, label in NAV_LINKS
    )
    return f"""<!doctype html>
<html lang="ru">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title} — Система управления семинарами</title>
    <link
        href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css"
        rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="/">
                Система управления семинарами
            </a>
            <ul class="navbar-nav">
                {nav_items}
            </ul>
        </div>
    </nav>
    <main class="container pb-5">
        {content}
    </main>
</body>
</html>"""
