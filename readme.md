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
- Django Forms (формы фильтрации, создания и редактирования)
- Pillow (загрузка изображений через `ImageField`)
- Django Admin (административная панель)
- Django Debug Toolbar (анализ SQL-запросов при разработке)
- Unidecode (транслитерация названий для адресов страниц)
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
| Новый семинар | `/seminars/create/` | Форма создания семинара с загрузкой изображения |
| Редактирование семинара | `/seminars/<slug>/edit/` | Форма изменения семинара, замена изображения |
| Карточка семинара | `/seminars/<slug>/` | Изображение, дата, занятость мест, программа докладов, участники; адрес вида `/seminars/freimvorki-1/` |
| Старый адрес семинара | `/seminars/<id>/` | Перенаправляет на адрес со slug |
| Список регистраций | `/registrations/` | Регистрации с фильтрами (статус, семинар, участник, дата), поиском, сортировкой и разбивкой на страницы |
| Карточка регистрации | `/registrations/<id>/` | Участник, семинар, статус, ссылка на семинар |
| Новая регистрация | `/registrations/create/` | Форма регистрации участника на семинар |
| Редактирование регистрации | `/registrations/<id>/edit/` | Форма изменения активной регистрации |
| Отмена регистрации | `/registrations/<id>/cancel/` | Только POST: меняет статус на «отменена» |
| Статистика | `/registrations/statistics/` | Регистрации по семинарам и участникам, популярные семинары, участники без регистраций |
| Административная панель | `/admin/` | Управление семинарами, докладами, участниками и регистрациями |

Для несуществующего идентификатора (`/seminars/9999/`,
`/registrations/9999/`) представление вызывает `get_object_or_404()`:
HTTP-ответ имеет статус 404 и выводится собственный шаблон `404.html`,
как и для любого несуществующего адреса.

Параметры списка регистраций (`/registrations/`):

| Параметр | Значения | Назначение |
|---|---|---|
| `status` | `active` (по умолчанию), `cancelled`, `completed`, `all` | фильтр по статусу |
| `seminar`, `participant` | идентификатор | фильтр по семинару и участнику |
| `date` | `ГГГГ-ММ-ДД` | фильтр по дате семинара |
| `q` | текст | поиск по имени и почте участника, названию семинара |
| `sort` | `date` (по умолчанию), `seminar`, `participant` | сортировка |
| `page` | номер | страница (по 5 записей) |

Параметры проверяет форма `RegistrationFilterForm`. Если хотя бы одно
значение некорректно (не дата, несуществующий семинар, неизвестный
статус или сортировка), фильтры не применяются: показывается список
по умолчанию, общее сообщение и ошибка под соответствующим полем.
Неверный номер страницы открывает первую страницу. Ссылки навигации по страницам сохраняют выбранные фильтры
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
  стилями, логотипом и JavaScript;

- создание и редактирование семинаров и регистраций через веб-формы,
  отмена регистрации, загрузка изображения семинара.

На данном этапе (ПР11) не реализовано — запланировано на следующие
практические работы:
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

## Django ORM (ПР9–ПР10)

### Модели
| Модель | Файл | Поля |
|---|---|---|
| `Seminar` — семинар | `seminars_app/models.py` | `title` (CharField), `seminar_date` (DateField), `max_participants` (PositiveIntegerField, с подсказкой `help_text`), `is_large` (GeneratedField), `slug` (SlugField, уникальный), `image` (ImageField, необязательное) |
| `Talk` — доклад | `seminars_app/models.py` | `seminar` (ForeignKey), `title`, `speaker` (CharField), `start_time` (TimeField), `duration_minutes` (PositiveIntegerField) |
| `Participant` — участник | `participants_app/models.py` | `name` (CharField), `email` (EmailField) |
| `Registration` — регистрация | `registrations_app/models.py` | `seminar` (ForeignKey), `participant` (ForeignKey), `status` (CharField с `TextChoices`, по умолчанию `active`) |

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
  изменение (`save(update_fields=["status"])`);
- `Registration.objects.active()`, `.cancelled()`, `.completed()`,
  `.for_date(date)` — методы пользовательского менеджера
  (`RegistrationQuerySet`); их можно соединять в цепочку, а
  `Registration.objects.all()` по-прежнему возвращает все записи;
- `Seminar.get_absolute_url()` — адрес страницы семинара на сайте;
- `Seminar.save()` — при первом сохранении создаёт `slug`.

### Статусы регистрации (ПР10)
Булево поле `is_cancelled` заменено полем `status` с перечислением
`Registration.Status` (`TextChoices`):

| Код в базе | Название | Занимает место |
|---|---|---|
| `active` | Активна | да |
| `cancelled` | Отменена | нет |
| `completed` | Завершена | нет |

Место на семинаре занимают только активные регистрации. Отмена и
завершение запись не удаляют. Статус «завершена» автоматически по
дате не выставляется — его задают в административной панели.

### Вычисляемое поле `is_large` (ПР10)
`Seminar.is_large` — `GeneratedField`: значение считает сама база
данных (`max_participants >= 30` — «крупный семинар») и хранит его в
таблице (`db_persist=True`). Вручную поле задать нельзя; при изменении
числа мест оно пересчитывается. Порог 30 — учебный пример.

### Адреса по slug (ПР10)
`Seminar.slug` формируется из названия: `unidecode()` переводит
русские буквы в латиницу, `slugify()` приводит строку к виду для
адреса, в конец добавляется идентификатор: «фреймворки» →
`freimvorki-1`. При переименовании семинара slug не меняется, чтобы
адрес страницы оставался прежним. Шаблоны и админка получают адрес
через `get_absolute_url()`, а не собирают его вручную.

### Контекстный процессор (ПР10)
`seminars_app/context_processors.py`, функция `seminar_context`,
подключена в `TEMPLATES["OPTIONS"]["context_processors"]`. Она
передаёт во все шаблоны `site_name` (название сайта) и
`seminars_total` (число семинаров). Эти переменные используются в
`base.html`, навигации («Семинары (2)») и на главной странице.

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
Файлы миграций хранятся в Git:

| Приложение | Миграция | Что делает |
|---|---|---|
| все три | `0001_initial` | создаёт таблицы (ПР9) |
| `registrations_app` | `0002_registration_status` | добавляет поле `status` |
| `registrations_app` | `0003_migrate_registration_statuses` | переносит данные: `is_cancelled` → `status` |
| `registrations_app` | `0004_remove_registration_is_cancelled` | удаляет старое поле |
| `seminars_app` | `0002_seminar_is_large_slug` | добавляет `is_large`, `slug`, подсказку к полю |
| `seminars_app` | `0003_populate_seminar_slugs` | заполняет `slug` у существующих семинаров |
| `seminars_app` | `0004_seminar_slug_unique` | делает `slug` уникальным |
| `seminars_app` | `0005_seminar_image_places_validator` | добавляет `image` и валидатор числа мест (ПР11) |

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
`0/1` — в статус `active` / `cancelled`. В конце скрипт печатает количество записей —
его нужно сверить с выводом `inspect_source_db.py`.

Проверка в Django shell (`python manage.py shell`):
```python
from registrations_app.models import Registration
for r in Registration.objects.select_related("seminar", "participant"):
    print(r.pk, r.seminar.title, r.participant.name, r.status)
```

### ORM-запросы проекта
| № | Запрос | Где используется | Приёмы |
|---|---|---|---|
| 1 | `Seminar.objects.with_places()` | список семинаров | получение набора, `annotate`, `Count`, `Q`, `F` |
| 2 | `get_object_or_404(Seminar.objects.with_places(), slug=...)` | карточка семинара | получение одного объекта |
| 3 | `.filter(title__icontains=query)` | список семинаров | поиск по строковому полю |
| 4 | `.order_by("seminar_date", "title")` | список семинаров | сортировка по нескольким полям |
| 5 | `seminar.talks.order_by("start_time")` | карточка семинара | обратная связь, сортировка по одному полю |
| 6 | `Participant.objects.filter(registrations__seminar=..., registrations__status=Registration.Status.ACTIVE)` | карточка семинара | фильтрация по полям связанной модели |
| 7 | `.filter(seminar_date__gte=..., free_places__gt=0)` | свободные места | несколько условий, условие по аннотации |
| 8 | `Registration.objects.active()`, `.cancelled()`, `.completed()` | список регистраций, главная | фильтрация по одному условию, методы менеджера |
| 9 | `.for_date(selected_date)` → `.filter(seminar__seminar_date=...)` | список регистраций | фильтрация по полю связанной модели |
| 10 | `.filter(seminar_id=...)`, `.filter(participant_id=...)` | список регистраций | фильтрация по внешним ключам |
| 11 | `.filter(Q(participant__name__icontains=q) \| Q(participant__email__icontains=q) \| Q(seminar__title__icontains=q))` | список регистраций | поиск по нескольким полям |
| 12 | `.annotate(seminar_title=F("seminar__title"), ...).values(...)` | список регистраций | данные связанных моделей, выбор полей |
| 13 | `.order_by(SORT_FIELDS[sort], "id")` | список регистраций | сортировка по полю связанной модели |
| 14 | `Paginator(registrations, 5).get_page(...)` | список регистраций | постраничный вывод |
| 15 | `get_object_or_404(Registration.objects.select_related("seminar", "participant"), pk=...)` | карточка регистрации | связанные объекты одним запросом |
| 16 | `Registration.objects.aggregate(total=Count("id"), active=..., cancelled=..., completed=...)` | статистика | сводные показатели |
| 17 | `Participant.objects.annotate(registrations_count=Count("registrations", filter=Q(...)))` | статистика | показатель по группам |
| 18 | `Seminar.objects.with_places().annotate(doubled_count=F("registered_count") * 2).filter(doubled_count__gte=F("max_participants"), ...)` | статистика | фильтрация по агрегату (аналог `HAVING`) |
| 19 | `Participant.objects.exclude(registrations__status=Registration.Status.ACTIVE)` | статистика | исключение записей |
| 20 | `Seminar.objects.count()`, `Participant.objects.count()` | контекстный процессор, главная | подсчёт записей |
| 21 | `Seminar.objects.filter(is_large=True)` | админка (фильтр списка) | фильтрация по вычисляемому полю |

Отменённые и завершённые регистрации не учитываются при подсчёте
занятых мест. Поле сортировки выбирается из словаря `SORT_FIELDS`:
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

## Формы (ПР11)

### Классы форм
| Форма | Файл | Тип | Назначение |
|---|---|---|---|
| `RegistrationFilterForm` | `registrations_app/forms.py` | `forms.Form` | фильтры списка регистраций (GET) |
| `RegistrationForm` | `registrations_app/forms.py` | `forms.ModelForm` | создание и редактирование регистрации |
| `SeminarSearchForm` | `seminars_app/forms.py` | `forms.Form` | поиск семинаров по названию (GET) |
| `AvailableSeminarsForm` | `seminars_app/forms.py` | `forms.Form` | поиск свободных мест по дате (GET) |
| `SeminarForm` | `seminars_app/forms.py` | `forms.ModelForm` | создание и редактирование семинара, загрузка изображения |

Обычная форма (`Form`) только проверяет и преобразует данные.
`ModelForm` связана с моделью: поля берутся из модели, а `save()`
создаёт или изменяет запись.

### Фильтрация списка регистраций
`RegistrationFilterForm` получает параметры из адресной строки:
`RegistrationFilterForm(request.GET or None)`. Без параметров форма
несвязанная (`is_bound = False`) и показывается пустой.

| Поле | Тип | Что проверяет Django |
|---|---|---|
| `q` | `CharField` | длину строки |
| `seminar`, `participant` | `ModelChoiceField` | что выбранный объект существует |
| `date` | `DateField` | что значение — дата; превращает строку в `date` |
| `status`, `sort` | `ChoiceField` | что значение входит в `choices` |

Все поля необязательные (`required=False`). Представление вызывает
`is_valid()` один раз и берёт значения из `cleaned_data` только после
успешной проверки. Номер страницы (`page`) в форму не входит: он
относится к пагинации. Исходная выборка по-прежнему строится методами
менеджера (`Registration.objects.active()` и другими), сортировка —
через словарь `SORT_FIELDS`.

### Создание и редактирование регистрации
`RegistrationForm` содержит только поля `seminar` и `participant`.
Поле `status` в форму не входит: новая регистрация получает статус
«активна» по умолчанию, а меняется он отдельной операцией отмены.
Даже если подставить `status` в запрос вручную, он будет проигнорирован.

| Правило | Где проверяется | Вид ошибки |
|---|---|---|
| нельзя регистрироваться на прошедший семинар | `RegistrationForm.clean_seminar()` | ошибка поля «Семинар» |
| участник не может быть зарегистрирован дважды | `RegistrationForm.clean()` | общая ошибка формы |
| на семинаре должно быть свободное место | представления, функция `seminar_has_free_place()` | общая ошибка формы (`form.add_error(None, ...)`) |

Свободные места считаются через `Registration.objects.active()`,
поэтому отменённые и завершённые регистрации место не занимают. При
редактировании сама запись исключается из проверок
(`.exclude(pk=...)`), иначе она мешала бы самой себе. Если семинар при
редактировании не менялся, запрет на прошедшую дату не применяется.

Представления:
- `registration_create` — GET показывает пустую форму, POST проверяет
  и сохраняет; кнопка «Зарегистрировать участника» на странице
  семинара передаёт `?seminar=<id>`, и семинар подставляется как
  начальное значение (`initial`);
- `registration_update` — та же форма с `instance=registration`;
  доступно только для активных регистраций, иначе ответ 404;
- `registration_cancel` — декоратор `@require_POST` (на GET ответ
  405), вызывает `registration.cancel()`; запись не удаляется.

После успешного сохранения выполняется перенаправление (`redirect`),
при ошибке форма показывается снова с введёнными значениями.

> Проверка мест выполняется перед сохранением. Если два запроса
> придут одновременно, оба могут пройти проверку — для учебного
> проекта это допустимо, в рабочей системе понадобились бы транзакции
> и ограничения на уровне базы данных.

### Создание и редактирование семинара, изображение
`SeminarForm` содержит поля `title`, `seminar_date`,
`max_participants`, `image`. Поля `slug` и `is_large` в форму не
входят: они заполняются автоматически.

- `clean_seminar_date()` — нельзя назначить семинар на прошедшую дату
  (у уже прошедшего семинара дату можно оставить прежней);
- `validate_places` (`seminars_app/validators.py`) — валидатор-функция:
  мест должно быть не меньше одного; подключён к полю модели, поэтому
  работает и в форме, и в админке;
- `ImageField` проверяет, что загруженный файл — изображение.

Загрузка изображения:
- модель: `image = models.ImageField(upload_to="seminars/", blank=True, null=True)`;
- настройки: `MEDIA_URL = "/media/"`, `MEDIA_ROOT = BASE_DIR / "media"`;
- шаблон формы: `enctype="multipart/form-data"`;
- представление: `SeminarForm(request.POST, request.FILES)`;
- раздача файлов при локальном запуске: маршрут `media/...` в
  `seminar_site/urls.py`;
- страница семинара: `{{ seminar.image.url }}` или текст
  «Изображение не загружено».

Файлы сохраняются в `media/seminars/`, в базе хранится только путь.
Каталог `media/` исключён из Git (`.gitignore`).

### Отображение форм и защита
- поля выводятся общим шаблоном `templates/includes/form_field.html`:
  подпись, элемент ввода, подсказка (`help_text`), ошибки поля;
- общие ошибки формы — `templates/includes/form_errors.html`
  (`form.non_field_errors`);
- оформление Bootstrap задаётся в виджетах (`form-control`,
  `form-select`), собственные стили — в `style.css`;
- каждая POST-форма содержит `{% csrf_token %}`; без токена сервер
  отвечает 403;
- операции, изменяющие данные (создание, редактирование, отмена),
  выполняются только POST-запросами.

## Административная панель (ПР10)
Адрес: `/admin/`. Для входа нужен суперпользователь:
```bash
python manage.py createsuperuser
```

Названия разделов заданы в `AppConfig.verbose_name` («Семинары»,
«Участники», «Регистрации»), названия моделей и полей — в
`verbose_name` моделей. Каждая модель зарегистрирована один раз
декоратором `@admin.register`.

| Модель | Настройки `ModelAdmin` |
|---|---|
| `Seminar` | столбцы: номер, название, дата, число мест, активных регистраций, «крупный семинар», ссылка на сайт; число мест редактируется в списке (`list_editable`); поиск по названию; фильтры по дате и признаку `is_large`; навигация по датам; `id`, `slug`, `is_large` только для чтения; доклады и регистрации в карточке (`TabularInline`); ссылка «Смотреть на сайте» |
| `Talk` | столбцы: номер, название, докладчик, семинар, время; поиск по названию, докладчику и семинару; фильтр по семинару |
| `Participant` | столбцы: номер, имя, почта; поиск по имени и почте; регистрации участника в карточке (`TabularInline`) |
| `Registration` | столбцы: номер, участник, семинар, дата семинара, число мест, статус; поиск по имени и почте участника и названию семинара; фильтры по статусу, дате и семинару; навигация по датам; выбор семинара и участника с поиском (`autocomplete_fields`); массовые действия |

Во всех списках заданы сортировка (`ordering`) и 20 записей на
странице (`list_per_page`).

Массовые действия для регистраций:
- «Отменить выбранные регистрации» — вызывает `cancel()` для каждой
  записи;
- «Вернуть в активные» — один запрос `queryset.update()`.

Оптимизация запросов в админке:
- `list_select_related = ("seminar", "participant")` — семинар и
  участник загружаются тем же запросом, что и список регистраций;
- число активных регистраций в списке семинаров считается аннотацией
  в `get_queryset()`, а не отдельным запросом на каждую строку.

> Админка не проверяет правила предметной области: через неё можно
> создать активную регистрацию на семинар, где мест уже нет, или
> зарегистрировать участника дважды. Эти правила проверяют
> пользовательские формы (раздел «Формы»). Удалить семинар или
> участника с регистрациями не даст `on_delete=PROTECT`.

Изображение семинара можно загрузить и заменить и в админке: поле
`image` входит в форму семинара автоматически.

## Анализ SQL-запросов (ПР10)
Django Debug Toolbar подключён в `settings.py` (приложение, middleware,
`INTERNAL_IPS`) и в `seminar_site/urls.py` (маршрут `__debug__/`).
Панель работает только при `DEBUG = True` и не подключается при
запуске автотестов. Она показывается справа на каждой странице сайта;
вкладка SQL содержит список запросов.

Число SQL-запросов на страницах:

| Страница | Запросов | Какие |
|---|---|---|
| `/` | 3 | число семинаров (контекстный процессор), участников, активных регистраций |
| `/seminars/` | 2 | список с подсчётом мест, число семинаров |
| `/seminars/<slug>/` | 4 | семинар, доклады, участники, число семинаров |
| `/seminars/available/?date=...` | 2 | свободные семинары, число семинаров |
| `/registrations/` | 5 | подсчёт для страниц, записи страницы, списки семинаров и участников для формы, число семинаров |
| `/registrations/<id>/` | 2 | регистрация с семинаром и участником (`select_related`), число семинаров |
| `/registrations/statistics/` | 6 | итоги, четыре выборки статистики, число семинаров |

Число запросов не зависит от количества записей (проблемы N+1 нет):
- список регистраций получает названия семинара и участника тем же
  запросом через `annotate()` с `F()` и `values()`;
- карточка регистрации использует `select_related()`;
- занятые места считаются аннотацией `Count(..., filter=Q(...))`.

Это закреплено автотестами с `assertNumQueries`.

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
├── media/                     # загруженные изображения (не в Git)
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
│       ├── navigation.html     # общая навигация
│       ├── form_field.html     # одно поле формы с ошибками
│       └── form_errors.html    # общие ошибки формы
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
│   ├── admin.py                # настройка админки
│   ├── context_processors.py   # общие данные для шаблонов
│   ├── forms.py                # формы поиска и форма семинара
│   ├── validators.py           # пользовательский валидатор
│   ├── tests.py                # тесты моделей и страниц
│   ├── views.py
│   ├── urls.py
│   └── templates/seminars/
│       ├── seminar_list.html
│       ├── seminar_detail.html
│       ├── seminar_form.html   # создание и редактирование
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
│   ├── forms.py                # форма фильтров и форма регистрации
│   ├── tests.py                # тесты списка, статистики, форм
│   ├── views.py
│   ├── urls.py
│   └── templates/registrations/
│       ├── registration_list.html
│       ├── registration_detail.html
│       ├── registration_form.html  # создание и редактирование
│       ├── statistics.html
│       └── includes/
│           ├── registration_status.html
│           └── cancel_form.html    # POST-форма отмены
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
- `{% if registration.status == "active" %}` — статус «Активна» /
  «Завершена» / «Отменена»;
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
| `seminars:detail` | `/seminars/<slug>/` |
| `seminars:detail_by_id` | `/seminars/<id>/` (перенаправление) |
| `seminars:create` | `/seminars/create/` |
| `seminars:update` | `/seminars/<slug>/edit/` |
| `registrations:list` | `/registrations/` |
| `registrations:statistics` | `/registrations/statistics/` |
| `registrations:detail` | `/registrations/<id>/` |
| `registrations:create` | `/registrations/create/` |
| `registrations:update` | `/registrations/<id>/edit/` |
| `registrations:cancel` | `/registrations/<id>/cancel/` (только POST) |

Статические маршруты (`create/`, `available/`, `statistics/`) стоят в
`urls.py` выше маршрутов с параметрами.

Пример: `{% url 'registrations:detail' registration.id %}`. Ссылки на
страницу семинара строятся методом модели:
`{{ item.get_absolute_url }}`.

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

Режим отладки задаётся переменной окружения: по умолчанию
`DEBUG = True`, запуск `DJANGO_DEBUG=0 python manage.py runserver`
выключает его (тогда видна собственная страница 404, а панель отладки
не подключается). При выключенной отладке сервер разработки сам не
раздаёт статику, поэтому в `seminar_site/urls.py` добавлен маршрут
`static/...` через `django.contrib.staticfiles.views.serve`
(только для локального запуска). Проверка поиска файла:
```bash
python manage.py findstatic homepage/img/logo.png
```

Загруженные пользователями изображения — это медиафайлы, а не
статика: они хранятся отдельно, в каталоге `media/` (см. раздел
«Формы»).

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
python manage.py createsuperuser     # учётная запись для /admin/
python manage.py runserver
```
Затем открыть в браузере `http://127.0.0.1:8000/`.

Консольная версия работает с JSON, веб-версия — с базой `db.sqlite3`
через Django ORM (см. раздел «Хранение данных»). Для входа в админку
(`/admin/`) нужен суперпользователь: `python manage.py createsuperuser`.

## Тестирование
```bash
python -m pytest -v        # консольная версия и слой ПР7
python manage.py test      # модели, ORM-запросы, страницы, формы, админка
```
Тесты Django (`seminars_app/tests.py`, `registrations_app/tests.py`)
работают на временной базе и проверяют: подсчёт мест без отменённых
регистраций, поиск свободных мест, фильтры, поиск, сортировку и
страницы списка регистраций, показатели статистики, ответ 404, защиту
от удаления (`PROTECT`) и перенос данных из базы ПР7. В ПР10
добавлены проверки: статусы регистраций и методы менеджера,
формирование slug и адреса страниц, перенаправление со старого адреса,
вычисляемое поле `is_large`, контекстный процессор, число SQL-запросов
на страницах, списки, поиск, фильтры и массовые действия админки.
В ПР11 добавлены проверки форм: состав полей, обязательные поля,
запрет прошедшей даты, запрет повторной регистрации, отсутствие мест,
редактирование без конфликта записи с самой собой, отмена только
POST-запросом (GET — 405), ответ 403 без CSRF-токена, ответ 404 для
отсутствующих и неактивных записей, некорректные GET-параметры
фильтров, загрузка изображения (файлы в тестах пишутся во временный
каталог).

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
`PR9: ...`, `PR10: ...`, `PR11: ...`).
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
сортировка и постраничный вывод списка регистраций), ПР10 (настройка
административной панели, статусы регистраций на `TextChoices`,
пользовательский менеджер, вычисляемое поле `GeneratedField`, адреса
семинаров по slug и `get_absolute_url()`, контекстный процессор,
Django Debug Toolbar и анализ SQL-запросов), ПР11 (формы Django:
фильтрация через `Form`, создание и редактирование регистраций и
семинаров через `ModelForm`, встроенная и пользовательская валидация,
отмена регистрации POST-запросом, CSRF-защита, загрузка изображений).

Веб-интерфейс получает и изменяет данные через Django ORM в базе
`db.sqlite3`. Участников и доклады пока можно добавлять только через
административную панель.

На следующих этапах планируется:
- реализация пользователей (регистрация и авторизация);
- формы для участников и докладов;
- разработка API;
- контейнеризация приложения;
- настройка CI/CD.

## Автор
Роднов Илья, группа ЭФБО-02-24, РТУ МИРЭА.
