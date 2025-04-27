-- database.sql

-- Удаляем таблицы в обратном порядке зависимостей (сначала checks, потом urls)
DROP TABLE IF EXISTS url_checks;
DROP TABLE IF EXISTS urls;

-- Создаем таблицу urls
CREATE TABLE urls (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    name VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаем таблицу url_checks
CREATE TABLE url_checks (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    url_id BIGINT REFERENCES urls (id) ON DELETE CASCADE NOT NULL,
    status_code INTEGER,
    h1 TEXT,
    title TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);