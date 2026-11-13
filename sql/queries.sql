-- ==========================================================
-- Система управления семинарами: SQL-запросы проекта
-- Проверка в консоли SQLite:  sqlite3 data/seminars.sqlite
-- В Django-представлениях значения вместо литералов передаются
-- параметрами (?), здесь указаны примеры для проверки.
-- ==========================================================


-- ==========================================================
-- 1. Выборка списков
-- ==========================================================

-- Запрос 1. Список семинаров, отсортированный по дате
SELECT
    id,
    title,
    seminar_date,
    max_participants
FROM seminars
ORDER BY seminar_date;

-- Запрос 2. Список участников, отсортированный по имени
SELECT
    id,
    name,
    email
FROM participants
ORDER BY name;


-- ==========================================================
-- 2. Фильтрация (WHERE)
-- ==========================================================

-- Запрос 3. Семинары, рассчитанные не менее чем на 3 участников
SELECT
    id,
    title,
    seminar_date,
    max_participants
FROM seminars
WHERE max_participants >= 3
ORDER BY max_participants;

-- Запрос 4. Активные (не отменённые) регистрации
SELECT
    id,
    seminar_id,
    participant_id
FROM registrations
WHERE is_cancelled = 0
ORDER BY id;

-- Запрос 5. Семинары, начиная с выбранной даты
SELECT
    id,
    title,
    seminar_date
FROM seminars
WHERE seminar_date >= '2026-10-01'
ORDER BY seminar_date;

-- Запрос 6. Программа семинара: доклады по времени начала
SELECT
    id,
    title,
    speaker,
    start_time,
    duration_minutes
FROM talks
WHERE seminar_id = 1
ORDER BY start_time;


-- ==========================================================
-- 3. Соединение таблиц (JOIN)
-- ==========================================================

-- Запрос 7. Полная информация об активных регистрациях:
-- вместо идентификаторов - название семинара и имя участника
SELECT
    registrations.id,
    seminars.title AS seminar_title,
    seminars.seminar_date,
    participants.name AS participant_name,
    participants.email
FROM registrations
JOIN seminars
    ON registrations.seminar_id = seminars.id
JOIN participants
    ON registrations.participant_id = participants.id
WHERE registrations.is_cancelled = 0
ORDER BY seminars.seminar_date, registrations.id;

-- Запрос 8. Участники выбранного семинара (активные регистрации)
SELECT
    participants.id,
    participants.name,
    participants.email
FROM registrations
JOIN participants
    ON registrations.participant_id = participants.id
WHERE registrations.seminar_id = 1
  AND registrations.is_cancelled = 0
ORDER BY participants.name;

-- Запрос 9. Все доклады с названиями семинаров
SELECT
    seminars.title AS seminar_title,
    seminars.seminar_date,
    talks.start_time,
    talks.title AS talk_title,
    talks.speaker
FROM talks
JOIN seminars
    ON talks.seminar_id = seminars.id
ORDER BY seminars.seminar_date, talks.start_time;


-- ==========================================================
-- 4. Агрегатные функции (COUNT)
-- ==========================================================

-- Запрос 10. Количество активных регистраций
SELECT
    COUNT(*) AS registrations_count
FROM registrations
WHERE is_cancelled = 0;

-- Запрос 11. Количество семинаров
SELECT
    COUNT(*) AS seminars_count
FROM seminars;

-- Запрос 12. Количество участников
SELECT
    COUNT(*) AS participants_count
FROM participants;


-- ==========================================================
-- 5. Группировка (GROUP BY, HAVING)
-- ==========================================================

-- Запрос 13. Количество активных регистраций и признак «мест нет»
-- по каждому семинару (LEFT JOIN: семинары без регистраций
-- остаются в результате со значением 0)
SELECT
    seminars.id,
    seminars.title,
    seminars.seminar_date,
    seminars.max_participants,
    COUNT(registrations.id) AS registered_count,
    (COUNT(registrations.id) >= seminars.max_participants) AS is_full
FROM seminars
LEFT JOIN registrations
    ON registrations.seminar_id = seminars.id
    AND registrations.is_cancelled = 0
GROUP BY
    seminars.id,
    seminars.title,
    seminars.seminar_date,
    seminars.max_participants
ORDER BY seminars.seminar_date;

-- Запрос 14. Количество активных регистраций каждого участника
SELECT
    participants.name,
    participants.email,
    COUNT(registrations.id) AS registrations_count
FROM participants
LEFT JOIN registrations
    ON registrations.participant_id = participants.id
    AND registrations.is_cancelled = 0
GROUP BY participants.id, participants.name, participants.email
ORDER BY registrations_count DESC, participants.name;

-- Востребованные семинары: заняты не менее половины мест
SELECT
    seminars.title,
    seminars.max_participants,
    COUNT(registrations.id) AS registered_count
FROM seminars
JOIN registrations
    ON registrations.seminar_id = seminars.id
WHERE registrations.is_cancelled = 0
GROUP BY seminars.id, seminars.title, seminars.max_participants
HAVING COUNT(registrations.id) * 2 >= seminars.max_participants
ORDER BY registered_count DESC, seminars.title;

-- Семинары со свободными местами, начиная с даты
SELECT
    seminars.id,
    seminars.title,
    seminars.seminar_date,
    seminars.max_participants,
    seminars.max_participants - COUNT(registrations.id) AS free_places
FROM seminars
LEFT JOIN registrations
    ON registrations.seminar_id = seminars.id
    AND registrations.is_cancelled = 0
WHERE seminars.seminar_date >= '2026-09-01'
GROUP BY
    seminars.id,
    seminars.title,
    seminars.seminar_date,
    seminars.max_participants
HAVING COUNT(registrations.id) < seminars.max_participants
ORDER BY seminars.seminar_date;

-- Запрос 17. Участники без активных регистраций (подзапрос)
SELECT
    id,
    name,
    email
FROM participants
WHERE id NOT IN (
    SELECT participant_id
    FROM registrations
    WHERE is_cancelled = 0
)
ORDER BY name;
