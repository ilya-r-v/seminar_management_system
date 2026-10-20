-- ==========================================
-- Система управления семинарами:
-- структура базы данных SQLite
-- ==========================================

-- Семинары
CREATE TABLE IF NOT EXISTS seminars (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    seminar_date TEXT NOT NULL,
    max_participants INTEGER NOT NULL
);

-- Участники
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL
);

-- Регистрации участников на семинары
-- (is_cancelled: 0 - активна, 1 - отменена)
CREATE TABLE IF NOT EXISTS registrations (
    id INTEGER PRIMARY KEY,
    seminar_id INTEGER NOT NULL,
    participant_id INTEGER NOT NULL,
    is_cancelled INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (seminar_id) REFERENCES seminars(id),
    FOREIGN KEY (participant_id) REFERENCES participants(id)
);

-- Доклады в программе семинара
CREATE TABLE IF NOT EXISTS talks (
    id INTEGER PRIMARY KEY,
    seminar_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    speaker TEXT NOT NULL,
    start_time TEXT NOT NULL,
    duration_minutes INTEGER NOT NULL,
    FOREIGN KEY (seminar_id) REFERENCES seminars(id)
);
