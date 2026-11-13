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
- SQLite, доступ к данным через Django ORM (модели и миграции)
- стандартный модуль `sqlite3` — слой ПР7 и перенос данных в базу Django
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
| Список семинаров | `/seminars/` | Все семинары с датой и статусом занятости мест, поиск по названию (`?q=`) |
| Свободные места | `/seminars/available/` | Поиск семинаров со свободными местами начиная с выбранной даты |
| Карточка семинара | `/seminars/<id>/` | Дата, занятость мест, программа докладов, участники |
| Список регистраций | `/registrations/` | Регистрации с фильтрами (статус, семинар, участник, дата), поиском, сортировкой и разбивкой на страницы |
| Карточка регистрации | `/registrations/<id>/` | Участник, семинар, статус, ссылка на семинар |
| Статистика | `/registrations/statistics/` | Регистрации по семинарам и участникам, популярные семинары, участники без регистраций |

Для несуществующего идентификатора (`/seminars/9999/`,
`/registrations/9999/`) представление вызывает `get_object_or_404()`:
HTTP-ответ имеет статус 404 и выводится собственный шаблон `404.html`,
как и для любого несуществующего адреса.

Параметры списка регистраций (`/registrations/`):

| Параметр | Значения | Назначение |
|---|---|---|
| `status` | `active` (по умолчанию), `cancelled`, `all` | фильтр по статусу |
| `seminar`, `participant` | идентификатор | фильтр по семинару и участнику |
| `date` | `ГГГГ-ММ-ДД` | фильтр по дате семинара |
| `q` | текст | поиск по имени и почте участника, названию семинара |
| `sort` | `date` (по умолчанию), `seminar`, `participant` | сортировка |
| `page` | номер | страница (по 5 записей) |

Некорректная дата даёт сообщение об ошибке, неизвестные значения
`status` и `sort` заменяются значениями по умолчанию, нечисловые
идентификаторы игнорируются, неверный номер страницы открывает первую
страницу. Ссылки навигации по страницам сохраняют выбранные фильтры
и сортировку (тег `{% querystring %}`).

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

На данном этапе (ПР9) не реализовано — запланировано на следующие
практические работы:
- Django Forms для создания и редактирования объектов через веб;
- регистрация и авторизация пользователей;
- API, контейнеризация, CI/CD.

## Хранение данных
В проекте три хранилища, у каждого своя роль:

| Файл | Кто использует | Роль |
|---|---|---|
| `db.sqlite3` | веб-интерфейс (Django ORM) | рабочая база приложения, таблицы создаются миграциями |
| `data/seminars.sqlite` | скрипты `db/` | исходная база ПР7, источник для переноса данных |
| `data/*.json` | консольное приложение `main.py` | данные консольной версии |

Веб-страницы получают данные только через Django ORM: представления
обращаются к менеджерам моделей, а результат передаётся в шаблоны
через контекст. Прямых SQL-запросов и чтения JSON в представлениях
больше нет.

`db.sqlite3` в репозиторий не входит (исключён в `.gitignore`): после
клонирования таблицы создаются командой `python manage.py migrate`, а
данные переносятся скриптом `python db/import_sqlite_to_orm.py`.

> Цепочка данных: консольное приложение пишет в JSON →
> `python3 -m db.import_json` переносит JSON в `data/seminars.sqlite` →
> `python db/import_sqlite_to_orm.py` переносит записи в `db.sqlite3`.
> Оба скрипта можно запускать повторно. Второй обновляет и добавляет
> записи по идентификатору, но не удаляет те, которых нет в источнике.

## Django ORM (ПР9)

### Модели
| Модель | Файл | Поля |
|---|---|---|
| `Seminar` — семинар | `seminars_app/models.py` | `title` (CharField), `seminar_date` (DateField), `max_participants` (PositiveIntegerField) |
| `Talk` — доклад | `seminars_app/models.py` | `seminar` (ForeignKey), `title`, `speaker` (CharField), `start_time` (TimeField), `duration_minutes` (PositiveIntegerField) |
| `Participant` — участник | `participants_app/models.py` | `name` (CharField), `email` (EmailField) |
| `Registration` — регистрация | `registrations_app/models.py` | `seminar` (ForeignKey), `participant` (ForeignKey), `is_cancelled` (BooleanField, по умолчанию `False`) |

Первичный ключ `id` Django создаёт автоматически. У каждой модели
заданы `__str__()`, сортировка по умолчанию (`Meta.ordering`) и
человекочитаемые названия. Модели зарегистрированы в админке.

`Participant` — участник предметной области, а не встроенный
пользователь Django. Классы из каталога `models/` относятся к
консольной версии и с Django ORM не связаны.

### Связи
| Связь | Поле | `on_delete` | Обратный доступ |
|---|---|---|---|
| семинар → регистрации (1:N) | `Registration.seminar` | `PROTECT` | `seminar.registrations` |
| участник → регистрации (1:N) | `Registration.participant` | `PROTECT` | `participant.registrations` |
| семинар → доклады (1:N) | `Talk.seminar` | `CASCADE` | `seminar.talks` |

`PROTECT` не даёт удалить семинар или участника, пока на них ссылаются
регистрации (сохраняется история). `CASCADE` удаляет доклады вместе с
семинаром: доклад без семинара не имеет смысла. Связь «многие ко
многим» между семинарами и участниками реализована моделью
`Registration`.

Методы моделей:
- `Seminar.objects.with_places()` — добавляет к семинарам
  `registered_count` (активные регистрации) и `free_places`; условие
  стоит внутри `Count(..., filter=Q(...))`, поэтому семинары без
  регистраций остаются в выборке (аналог `LEFT JOIN` из ПР7);
- `Registration.cancel()` — отменяет регистрацию и сохраняет
  изменение (`save(update_fields=["is_cancelled"])`).

Правило «нельзя зарегистрироваться, если мест нет» проверяется в
консольной версии; в веб-версии создание записей через формы будет
добавлено в следующих работах.

### Миграции
Выбрана стратегия «таблицы, управляемые Django, и перенос данных»:
исходная база ПР7 не изменяется, Django создаёт свои таблицы в
`db.sqlite3`.
```bash
python manage.py makemigrations          # создать файлы миграций
python manage.py showmigrations          # состояние миграций
python manage.py sqlmigrate seminars_app 0001   # SQL миграции
python manage.py migrate                 # применить миграции
python manage.py makemigrations --check  # нет ли несозданных миграций
```
Файлы миграций (`*/migrations/0001_initial.py`) хранятся в Git.

### Перенос данных из базы ПР7
```bash
cp data/seminars.sqlite data/seminars_backup.sqlite   # резервная копия
python db/inspect_source_db.py       # таблицы, столбцы, число записей
python manage.py migrate             # таблицы в db.sqlite3
python db/import_sqlite_to_orm.py    # перенос через ORM
```
`db/import_sqlite_to_orm.py` читает `data/seminars.sqlite` и создаёт
записи методом `update_or_create()` в одной транзакции
(`transaction.atomic()`). Сначала переносятся семинары и участники,
затем регистрации и доклады, которые на них ссылаются. Идентификаторы
сохраняются, строки дат и времени превращаются в `date` и `time`,
`0/1` — в `False/True`. В конце скрипт печатает количество записей —
его нужно сверить с выводом `inspect_source_db.py`.

Проверка в Django shell (`python manage.py shell`):
```python
from registrations_app.models import Registration
for r in Registration.objects.select_related("seminar", "participant"):
    print(r.pk, r.seminar.title, r.participant.name, r.is_cancelled)
```

### ORM-запросы проекта
| № | Запрос | Где используется | Приёмы |
|---|---|---|---|
| 1 | `Seminar.objects.with_places()` | список семинаров | получение набора, `annotate`, `Count`, `Q`, `F` |
| 2 | `get_object_or_404(Seminar.objects.with_places(), pk=...)` | карточка семинара | получение одного объекта |
| 3 | `.filter(title__icontains=query)` | список семинаров | поиск по строковому полю |
| 4 | `.order_by("seminar_date", "title")` | список семинаров | сортировка по нескольким полям |
| 5 | `seminar.talks.order_by("start_time")` | карточка семинара | обратная связь, сортировка по одному полю |
| 6 | `Participant.objects.filter(registrations__seminar=..., registrations__is_cancelled=False)` | карточка семинара | фильтрация по полям связанной модели |
| 7 | `.filter(seminar_date__gte=..., free_places__gt=0)` | свободные места | несколько условий, условие по аннотации |
| 8 | `Registration.objects.filter(is_cancelled=False)` | список регистраций, главная | фильтрация по одному условию |
| 9 | `.filter(seminar__seminar_date=...)` | список регистраций | фильтрация по полю связанной модели |
| 10 | `.filter(seminar_id=...)`, `.filter(participant_id=...)` | список регистраций | фильтрация по внешним ключам |
| 11 | `.filter(Q(participant__name__icontains=q) \| Q(participant__email__icontains=q) \| Q(seminar__title__icontains=q))` | список регистраций | поиск по нескольким полям |
| 12 | `.annotate(seminar_title=F("seminar__title"), ...).values(...)` | список регистраций | данные связанных моделей, выбор полей |
| 13 | `.order_by(SORT_FIELDS[sort], "id")` | список регистраций | сортировка по полю связанной модели |
| 14 | `Paginator(registrations, 5).get_page(...)` | список регистраций | постраничный вывод |
| 15 | `get_object_or_404(Registration.objects.select_related("seminar", "participant"), pk=...)` | карточка регистрации | связанные объекты одним запросом |
| 16 | `Registration.objects.aggregate(total=Count("id"), active=..., cancelled=...)` | статистика | сводные показатели |
| 17 | `Participant.objects.annotate(registrations_count=Count("registrations", filter=Q(...)))` | статистика | показатель по группам |
| 18 | `Seminar.objects.with_places().annotate(doubled_count=F("registered_count") * 2).filter(doubled_count__gte=F("max_participants"), ...)` | статистика | фильтрация по агрегату (аналог `HAVING`) |
| 19 | `Participant.objects.exclude(registrations__is_cancelled=False)` | статистика | исключение записей |
| 20 | `Seminar.objects.count()`, `Participant.objects.count()` | главная | подсчёт записей |

Отменённые регистрации не учитываются при подсчёте занятых мест и в
статистике. Поле сортировки выбирается из словаря `SORT_FIELDS`:
произвольный текст из адреса в `order_by()` не попадает.

> Особенность SQLite: поиск `icontains` не различает регистр только
> для латинских букв. Для кириллицы регистр учитывается: запрос
> «иван» не найдёт участника «Иван».

### Представления
| Представление | Что делает |
|---|---|
| `homepage.views.index` | сводка: число семинаров, участников, активных регистраций |
| `seminars_app.views.seminar_list` | список семинаров с занятостью мест и поиском |
| `seminars_app.views.seminar_detail` | семинар, программа докладов, участники |
| `seminars_app.views.available_seminars` | поиск семинаров со свободными местами по дате |
| `registrations_app.views.registration_list` | фильтры, поиск, сортировка, страницы |
| `registrations_app.views.registration_detail` | одна регистрация со связанными объектами |
| `registrations_app.views.statistics` | итоги и показатели по семинарам и участникам |

## База данных (ПР7)
Слой ПР7 сохранён как предыдущая реализация: `sql/schema.sql`,
`sql/queries.sql`, `db/database.py`, `db/import_json.py` и база
`data/seminars.sqlite`. Представления их больше не используют; база
служит источником для переноса данных в `db.sqlite3`.

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

### Представления ПР7 (заменены на ORM в ПР9)
В ПР7 эти представления выполняли SQL-запросы через `sqlite3`:

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
├── db/                        # скрипты работы с базами
│   ├── __init__.py
│   ├── database.py            # ПР7: подключение, init_db, fetch_all/fetch_one
│   ├── import_json.py         # ПР7: импорт JSON → data/seminars.sqlite
│   ├── inspect_source_db.py   # ПР9: просмотр структуры исходной базы
│   └── import_sqlite_to_orm.py  # ПР9: перенос данных в базу Django
├── sql/
│   ├── schema.sql             # структура таблиц
│   └── queries.sql            # 17 учебных SQL-запросов
├── data/                      # данные
│   ├── seminars.sqlite        # исходная база ПР7
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
├── db.sqlite3                 # база Django (создаётся миграциями, не в Git)
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
├── seminars_app/               # Django-приложение: семинары и доклады
│   ├── models.py               # модели Seminar и Talk
│   ├── migrations/             # миграции
│   ├── admin.py
│   ├── tests.py                # тесты моделей и страниц
│   ├── views.py
│   ├── urls.py
│   └── templates/seminars/
│       ├── seminar_list.html
│       ├── seminar_detail.html
│       ├── available.html
│       └── includes/
│           └── seminar_card.html
├── participants_app/           # Django-приложение: участники
│   ├── models.py               # модель Participant
│   ├── migrations/
│   └── admin.py
├── registrations_app/          # Django-приложение: регистрации
│   ├── models.py               # модель Registration
│   ├── migrations/
│   ├── admin.py
│   ├── tests.py                # тесты списка, статистики, переноса
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
  предметной области консольной версии.
- `seminars_app/models.py`, `participants_app/models.py`,
  `registrations_app/models.py` — модели Django ORM веб-версии.
- `storage.py` — чтение/запись JSON, преобразование между словарями и
  объектами.
- `utils.py` — валидированный ввод данных в консольном режиме.
- `webdata.py` — обёртка над `storage.py` из ПР5 (веб-слоем больше не
  используется).
- `homepage/views.py`, `seminars_app/views.py`,
  `registrations_app/views.py` — функции-представления Django: получают
  данные через Django ORM, готовят словарь контекста и вызывают
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
context = {"registration": registration}
return render(request, "registrations/registration_detail.html", context)
```
Для списка семинаров ORM-запрос заранее считает число активных
регистраций и свободных мест (`seminar_items`), а шаблон только
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
python manage.py migrate             # создать таблицы в db.sqlite3
python db/import_sqlite_to_orm.py    # перенести данные из базы ПР7
python manage.py runserver
```
Затем открыть в браузере `http://127.0.0.1:8000/`.

Консольная версия работает с JSON, веб-версия — с базой `db.sqlite3`
через Django ORM (см. раздел «Хранение данных»). Для входа в админку
(`/admin/`) нужен суперпользователь: `python manage.py createsuperuser`.

## Тестирование
```bash
python -m pytest -v        # консольная версия и слой ПР7
python manage.py test      # модели, ORM-запросы и страницы (ПР9)
```
Тесты Django (`seminars_app/tests.py`, `registrations_app/tests.py`)
работают на временной базе и проверяют: подсчёт мест без отменённых
регистраций, поиск свободных мест, фильтры, поиск, сортировку и
страницы списка регистраций, показатели статистики, ответ 404, защиту
от удаления (`PROTECT`) и перенос данных из базы ПР7.

Тесты `tests/test_database.py` проверяют схему, внешние ключи, импорт
и выполнение `queries.sql`. Остальные тесты покрывают классы `Seminar`, `Participant`, `Registration`, `Talk`
и их основные сценарии (добавление, поиск, регистрация с проверкой
мест, отмена регистрации, запрет повторной регистрации).

## Проверка качества кода
```bash
python manage.py check
python manage.py makemigrations --check
python manage.py showmigrations
flake8 . --extend-exclude=venv
mypy main.py
```
Файл `setup.cfg` исключает `.venv`, `__pycache__`, `.git` и
автоматически созданные файлы миграций из проверки flake8, чтобы линтер не сканировал код сторонних библиотек внутри
виртуального окружения.

## Git
Репозиторий ведётся с коммитами, соответствующими номеру практической
работы (например, `PR1: ...`, `PR2: ...`, `PR3: ...`, `PR5: ...`,
`PR6: ...`, `PR7: add SQLite database and SQL queries`,
`PR9: ...`).
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
представления на SQL с `sqlite3.Row`, страницы поиска и статистики),
ПР9 (модели Django ORM и связи между ними, миграции, перенос данных
из базы ПР7, перевод всех представлений на ORM, фильтрация, поиск,
сортировка и постраничный вывод списка регистраций).

Веб-интерфейс получает данные через Django ORM из базы `db.sqlite3`.
Django Forms пока не используются, поэтому в вебе данные только
просматриваются (изменять их можно через админку или Django shell).

На следующих этапах планируется:
- реализация пользователей (регистрация и авторизация);
- создание и редактирование объектов через Django Forms;
- разработка API;
- контейнеризация приложения;
- настройка CI/CD.

## Автор
Роднов Илья, группа ЭФБО-02-24, РТУ МИРЭА.
