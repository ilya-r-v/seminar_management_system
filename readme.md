# Система управления семинарами

## Назначение
Приложение для учёта семинаров, участников, их регистраций и программы
докладов. Позволяет создавать семинары, регистрировать на них участников
с контролем количества свободных мест, отменять регистрации и вести
расписание докладов внутри каждого семинара.

## Целевая аудитория
Организаторы учебных и профессиональных семинаров (например, сотрудники
вуза или образовательного центра), которым нужно вести учёт мероприятий
и участников без дорогостоящих коммерческих систем.

## Предметная область
Организация семинаров: у каждого семинара есть тема, дата и ограничение
по числу участников. Участники регистрируются на семинары, при этом
система не допускает превышения вместимости и повторной регистрации
одного и того же участника на один и тот же семинар. В рамках семинара
ведётся программа — список докладов с докладчиками и временем.

## Технологии
- Python 3
- Django 5.2 (веб-интерфейс)
- Django Template Language (шаблоны страниц)
- HTML5, CSS3, JavaScript (собственные статические файлы)
- Bootstrap 5.3 (базовая вёрстка, подключается через CDN)
- pytest, flake8, mypy (тестирование и контроль качества кода)
- SQLite и стандартный модуль `sqlite3` (база данных и SQL-запросы)
- JSON-файлы — исходные данные и хранилище консольной версии

## Основные сущности
- **Seminar (Семинар)** — `id`, `title`, `date`, `max_participants`.
- **Participant (Участник)** — `id`, `name`, `email`.
- **Registration (Регистрация)** — `id`, `seminar`, `participant`,
  `is_cancelled`.
- **Talk (Доклад)** — `id`, `seminar`, `title`, `speaker`, `start_time`,
  `duration_minutes`.

## Страницы веб-интерфейса
| Страница | URL | Описание |
|---|---|---|
| Главная | `/` | Краткая сводка: число семинаров, участников, активных регистраций |
| Список семинаров | `/seminars/` | Все семинары с датой и статусом занятости мест |
| Свободные места | `/seminars/available/` | Поиск семинаров со свободными местами начиная с выбранной даты |
| Карточка семинара | `/seminars/<id>/` | Дата, занятость мест, программа докладов, участники |
| Список регистраций | `/registrations/` | Активные регистрации (`?all=1` — все, включая отменённые) |
| Карточка регистрации | `/registrations/<id>/` | Участник, семинар, статус, ссылка на семинар |
| Статистика | `/registrations/statistics/` | Регистрации по семинарам и участникам, популярные семинары, участники без регистраций |

Для несуществующего идентификатора (`/seminars/9999/`,
`/registrations/9999/`) выводится страница «Семинар не найден» /
«Регистрация не найдена», а HTTP-ответ имеет статус 404. Для любого
несуществующего адреса используется собственный шаблон `404.html`.

Все страницы формируются Django-шаблонами: представления только
готовят данные и передают их в шаблон через контекст. Функция `page()`
из ПР5, собиравшая HTML-строки в Python, удалена.

## Основные функции
Реализовано:
- добавление семинара, поиск по названию, просмотр списка семинаров;
- регистрация участника на семинар с проверкой свободных мест и запретом
  повторной регистрации;
- отмена регистрации;
- добавление докладов и просмотр программы семинара;
- веб-страницы: главная, список и карточка семинара, список и карточка
  регистрации — на Django-шаблонах, с общей навигацией, собственными
  стилями, логотипом и JavaScript.

На данном этапе (ПР6) не реализовано — запланировано на следующие
практические работы:
- перенос сущностей на Django ORM и подключение базы данных;
- Django Forms для создания и редактирования объектов через веб;
- регистрация и авторизация пользователей;
- API, контейнеризация, CI/CD.

## Хранение данных
Данные хранятся в двух местах:
- JSON-файлы в `data/` (`seminars.json`, `participants.json`,
  `registrations.json`, `talks.json`) — их используют консольное
  приложение (`main.py`) и скрипт импорта;
- база SQLite `data/seminars.sqlite` — из неё читает веб-интерфейс.

Веб-страницы получают данные только SQL-запросами через `sqlite3`
(`sqlite3.Row`, обращение к полям по имени), результат передаётся в
существующие шаблоны через контекст. SQL на страницах не отображается.

> Консольное приложение пишет в JSON, а веб-интерфейс читает SQLite.
> Чтобы синхронизировать их, повторно запустите импорт:
> `python3 -m db.import_json` (он очищает таблицы и загружает данные
> заново, поэтому его можно запускать сколько угодно раз).

## База данных (ПР7)

### Таблицы (`sql/schema.sql`)
**seminars** — семинары
| Поле | Тип | Ограничения |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| title | TEXT | NOT NULL |
| seminar_date | TEXT (`YYYY-MM-DD`) | NOT NULL |
| max_participants | INTEGER | NOT NULL |

**participants** — участники
| Поле | Тип | Ограничения |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| name | TEXT | NOT NULL |
| email | TEXT | NOT NULL |

**registrations** — регистрации участников на семинары
| Поле | Тип | Ограничения |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| seminar_id | INTEGER | NOT NULL, FOREIGN KEY → seminars(id) |
| participant_id | INTEGER | NOT NULL, FOREIGN KEY → participants(id) |
| is_cancelled | INTEGER (0/1) | NOT NULL, DEFAULT 0 |

**talks** — доклады в программе семинара
| Поле | Тип | Ограничения |
|---|---|---|
| id | INTEGER | PRIMARY KEY |
| seminar_id | INTEGER | NOT NULL, FOREIGN KEY → seminars(id) |
| title | TEXT | NOT NULL |
| speaker | TEXT | NOT NULL |
| start_time | TEXT | NOT NULL |
| duration_minutes | INTEGER | NOT NULL |

Связи: один семинар — много регистраций и докладов; один участник —
много регистраций (связь «многие ко многим» между семинарами и
участниками реализована таблицей `registrations`). Внешние ключи
включаются командой `PRAGMA foreign_keys = ON` при каждом подключении.

### Пакет `db/`
- `db/database.py` — путь к базе, `get_connection()`, `init_db()`
  (выполняет `schema.sql`), `fetch_all()` и `fetch_one()`;
- `db/import_json.py` — импорт данных из JSON в SQLite.

### Создание базы и импорт данных
```bash
python3 -m db.import_json
```
Скрипт создаёт `data/seminars.sqlite` по `sql/schema.sql` и загружает
в неё данные из JSON. Просмотреть базу вручную:
```bash
sqlite3 data/seminars.sqlite
```

### SQL-запросы (`sql/queries.sql`, 17 запросов)
| Группа | Запросы |
|---|---|
| Выборка списков | 1 — семинары, 2 — участники |
| Фильтрация (WHERE) | 3 — семинары с большим числом мест, 4 — активные регистрации, 5 — семинары от даты, 6 — доклады семинара |
| JOIN | 7 — регистрации с участником и семинаром, 8 — участники семинара, 9 — доклады с названиями семинаров |
| COUNT | 10 — активные регистрации, 11 — семинары, 12 — участники |
| GROUP BY / HAVING | 13 — семинары с числом занятых мест, 14 — регистрации по участникам, 15 — популярные семинары, 16 — семинары со свободными местами от даты |
| Подзапросы | 17 — участники без активных регистраций |

### Представления, работающие с SQLite
| Представление | Что делает |
|---|---|
| `homepage.views.index` | три COUNT-запроса для сводки на главной |
| `seminars_app.views.seminar_list` | список семинаров с занятостью мест (LEFT JOIN + GROUP BY) |
| `seminars_app.views.seminar_detail` | семинар, программа докладов, участники (JOIN) |
| `seminars_app.views.available_seminars` | поиск семинаров со свободными местами по дате |
| `registrations_app.views.registration_list` | активные или все регистрации (JOIN трёх таблиц) |
| `registrations_app.views.registration_detail` | одна регистрация |
| `registrations_app.views.statistics` | статистика (GROUP BY, HAVING, подзапрос) |

Пользовательские сценарии: просмотр списка семинаров; просмотр
программы и участников семинара; просмотр активных регистраций;
поиск свободных мест по дате; просмотр статистики.

## Структура проекта
```
seminar-management-system/
├── main.py                  # консольное приложение (ПР1–ПР3)
├── storage.py                # загрузка/сохранение JSON
├── utils.py                  # ввод данных с валидацией
├── webdata.py                 # загрузка данных для веб-слоя (ПР5)
├── models/                   # классы предметной области
│   ├── __init__.py
│   ├── seminars.py
│   ├── participants.py
│   ├── registrations.py
│   └── talks.py
├── db/                        # слой SQLite (ПР7)
│   ├── __init__.py
│   ├── database.py            # подключение, init_db, fetch_all/fetch_one
│   └── import_json.py         # импорт JSON → SQLite
├── sql/
│   ├── schema.sql             # структура таблиц
│   └── queries.sql            # 17 учебных SQL-запросов
├── data/                      # данные
│   ├── seminars.sqlite        # база SQLite
│   ├── seminars.json
│   ├── participants.json
│   ├── registrations.json
│   └── talks.json
├── tests/                     # тесты pytest для консольной версии
│   ├── test_seminars.py
│   ├── test_participants.py
│   ├── test_registrations.py
│   ├── test_talks.py
│   └── test_database.py        # тесты слоя SQLite
├── manage.py                  # управляющий скрипт Django
├── seminar_site/              # конфигурация Django-проекта
│   ├── settings.py
│   ├── urls.py                # корневые маршруты (include по приложениям)
│   ├── wsgi.py
│   └── asgi.py
├── templates/                  # шаблоны уровня проекта
│   ├── base.html               # базовый шаблон всех страниц
│   ├── 404.html                # страница «Страница не найдена»
│   └── includes/
│       └── navigation.html     # общая навигация
├── homepage/                   # Django-приложение: главная страница
│   ├── views.py
│   ├── urls.py
│   ├── templates/homepage/
│   │   └── index.html
│   └── static/homepage/
│       ├── css/style.css       # собственные стили проекта
│       ├── js/main.js          # текущий год в подвале
│       └── img/logo.png        # логотип
├── seminars_app/               # Django-приложение: страницы семинаров
│   ├── views.py
│   ├── urls.py
│   └── templates/seminars/
│       ├── seminar_list.html
│       ├── seminar_detail.html
│       ├── available.html
│       └── includes/
│           └── seminar_card.html
├── registrations_app/          # Django-приложение: страницы регистраций
│   ├── views.py
│   ├── urls.py
│   └── templates/registrations/
│       ├── registration_list.html
│       ├── registration_detail.html
│       ├── statistics.html
│       └── includes/
│           └── registration_status.html
├── requirements.txt
├── setup.cfg                  # настройки flake8
└── README.md
```

## Назначение модулей
- `models/seminars.py`, `models/participants.py`,
  `models/registrations.py`, `models/talks.py` — классы и функции
  предметной области (используются и консолью, и веб-слоем).
- `storage.py` — чтение/запись JSON, преобразование между словарями и
  объектами.
- `utils.py` — валидированный ввод данных в консольном режиме.
- `webdata.py` — тонкая обёртка над `storage.py` для веб-представлений.
- `homepage/views.py`, `seminars_app/views.py`,
  `registrations_app/views.py` — функции-представления Django: читают
  данные через `webdata.py`, готовят словарь контекста и вызывают
  `render()`. HTML во views не формируется.
- `templates/`, `*/templates/` — Django-шаблоны страниц.
- `homepage/static/homepage/` — собственные CSS, JavaScript и логотип.

## Django Template Language
### Базовый шаблон и наследование
`templates/base.html` содержит общую структуру страницы: объявление
документа, кодировку, подключение Bootstrap и собственного CSS,
навигацию, основной контейнер, подвал и подключение JavaScript.
В нём объявлены блоки, которые переопределяют дочерние страницы:
```
{% block title %}...{% endblock %}
{% block content %}...{% endblock %}
```
Каждая страница наследует базовый шаблон через
`{% extends "base.html" %}` и не дублирует общую разметку.

### Включаемые шаблоны
Повторяющиеся фрагменты вынесены в отдельные файлы и подключаются
через `{% include %}`:
- `templates/includes/navigation.html` — навигация (подключается в
  `base.html`);
- `seminars/includes/seminar_card.html` — карточка семинара в списке;
- `registrations/includes/registration_status.html` — статус
  регистрации; один и тот же фрагмент используется и в списке, и на
  странице регистрации.

### Контекст
Представления передают данные в шаблон словарём контекста, например:
```python
context = {"registrations": get_registrations()}
return render(request, "registrations/registration_list.html", context)
```
Для списка семинаров представление заранее считает число активных
регистраций и признак «мест нет» (`seminar_items`), а шаблон только
выводит готовые значения.

### Циклы и условия
- `{% for ... %}` / `{% empty %}` — списки семинаров, регистраций и
  программы докладов с сообщением для пустой коллекции;
- `{% if registration.is_cancelled %}` — статус «Активна» / «Отменена»;
- `{% if item.is_full %}` — цвет индикатора занятости мест;
- `{% if seminar %}` / `{% if registration %}` — вывод страницы
  «не найдено», при этом view возвращает статус 404;
- подсветка активного пункта меню по
  `request.resolver_match.namespace`.

### Фильтры шаблонов
- `{{ seminar_items|length }}`, `{{ registrations|length }}`,
  `{{ seminars|length }}` — количество элементов;
- `{{ seminar.title|default:"Без названия" }}` — значение по умолчанию;
- `{{ seminar.date|date:"d.m.Y" }}` — формат даты.

Фильтры используются только для представления данных, бизнес-логики
в шаблонах нет.

## URL-маршрутизация
У каждого приложения задано пространство имён (`app_name`), ссылки в
шаблонах строятся через `{% url %}`, а не жёстко заданными адресами:

| Имя маршрута | Адрес |
|---|---|
| `homepage:index` | `/` |
| `seminars:list` | `/seminars/` |
| `seminars:available` | `/seminars/available/` |
| `seminars:detail` | `/seminars/<id>/` |
| `registrations:list` | `/registrations/` |
| `registrations:statistics` | `/registrations/statistics/` |
| `registrations:detail` | `/registrations/<id>/` |

Пример: `{% url 'seminars:detail' item.seminar.id %}`.

## Статические файлы
Каталог `homepage/static/homepage/`:
- `css/style.css` — собственное оформление (шапка, логотип, карточки
  статистики и семинаров, статусы регистраций, подвал);
- `js/main.js` — выводит текущий год в подвале страницы;
- `img/logo.png` — логотип в навигации.

В `base.html` используется `{% load static %}` и
`{% static 'homepage/css/style.css' %}` и т.д. Каталог шаблонов уровня
проекта подключён в `settings.py`
(`TEMPLATES["DIRS"] = [BASE_DIR / "templates"]`).

Так как в проекте `DEBUG = False`, сервер разработки сам не раздаёт
статику, поэтому в `seminar_site/urls.py` добавлен маршрут
`static/...` через `django.contrib.staticfiles.views.serve`
(только для локального запуска). Проверка поиска файла:
```bash
python manage.py findstatic homepage/img/logo.png
```

## Запуск
### Консольная версия
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Веб-версия (Django)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m db.import_json
python manage.py runserver
```
Затем открыть в браузере `http://127.0.0.1:8000/`.

Консольная версия работает с JSON, веб-версия — с `data/seminars.sqlite`
(см. раздел «Хранение данных»).

## Тестирование
```bash
python -m pytest -v
```
Тесты `tests/test_database.py` проверяют схему, внешние ключи, импорт
и выполнение `queries.sql`. Остальные тесты покрывают классы `Seminar`, `Participant`, `Registration`, `Talk`
и их основные сценарии (добавление, поиск, регистрация с проверкой
мест, отмена регистрации, запрет повторной регистрации).

## Проверка качества кода
```bash
python manage.py check
flake8 . --extend-exclude=venv
mypy main.py
```
Файл `setup.cfg` исключает `.venv`, `__pycache__` и `.git` из проверки
flake8, чтобы линтер не сканировал код сторонних библиотек внутри
виртуального окружения.

## Git
Репозиторий ведётся с коммитами, соответствующими номеру практической
работы (например, `PR1: ...`, `PR2: ...`, `PR3: ...`, `PR5: ...`,
`PR6: ...`, `PR7: add SQLite database and SQL queries`).
Перед коммитом рекомендуется проверить состояние рабочего дерева
(`git status`), прогнать тесты и линтер, затем зафиксировать изменения
(`git add`, `git commit`) и отправить их в удалённый репозиторий
(`git push`), если он подключён.

## Текущее состояние и план развития
Выполнено: ПР1 (консольный сценарий), ПР2 (коллекции, функции, модули,
JSON-хранилище, тесты), ПР3 (ООП-рефакторинг), ПР5 (веб-интерфейс на
Django поверх консольного приложения без базы данных), ПР6 (перевод
веб-интерфейса на Django-шаблоны: базовый шаблон, наследование, блоки,
include, контекст, циклы и условия, фильтры, именованные URL и
пространства имён, собственные CSS, JavaScript и изображение), ПР7
(база данных SQLite, `schema.sql`, импорт из JSON, 17 SQL-запросов,
представления на SQL с `sqlite3.Row`, страницы поиска и статистики).

Веб-интерфейс читает данные из SQLite через чистый SQL; Django ORM и
Django Forms пока не используются, поэтому в вебе данные только
просматриваются.

На следующих этапах планируется:
- перенос сущностей в Django ORM;
- реализация пользователей (регистрация и авторизация);
- создание и редактирование объектов через Django Forms;
- разработка API;
- контейнеризация приложения;
- настройка CI/CD.