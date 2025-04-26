-- database.sql

-- Удаляем таблицу urls, если она вдруг уже существует (для удобства при перезапусках)
DROP TABLE IF EXISTS urls;

-- Создаем таблицу urls
CREATE TABLE urls (
    -- Идентификатор сайта, первичный ключ
    -- BIGINT - для больших чисел, PRIMARY KEY - первичный ключ
    -- GENERATED ALWAYS AS IDENTITY - автоматически генерируемое значение (как автоинкремент)
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,

    -- Имя сайта (нормализованный URL)
    -- VARCHAR(255) - строка до 255 символов
    -- UNIQUE - значение должно быть уникальным в таблице (нельзя добавить два одинаковых URL)
    -- NOT NULL - значение не может быть пустым
    name VARCHAR(255) UNIQUE NOT NULL,

    -- Дата добавления сайта
    -- TIMESTAMP - тип данных для даты и времени
    -- DEFAULT CURRENT_TIMESTAMP - значение по умолчанию будет текущее время добавления записи
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);