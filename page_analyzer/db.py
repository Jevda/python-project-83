# page_analyzer/db.py

import os
import psycopg
from dotenv import load_dotenv
from datetime import date # Для created_at

# Загрузка переменных окружения
load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    """Устанавливает соединение с базой данных PostgreSQL."""
    try:
        # Установка соединения по DATABASE_URL
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except psycopg.Error as e:
        # Обработка ошибок подключения
        print(f"Ошибка подключения к базе данных: {e}")
        raise # Перевыброс исключения


def get_url_by_id(url_id):
    """Находит URL в базе данных по его ID."""
    conn = get_db_connection()
    url_data = None
    try:
        # Использование 'with' для автоматического управления курсором
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
            url_data = cur.fetchone() # Получение одной строки или None
    finally:
        # Гарантированное закрытие соединения
        if conn:
            conn.close()
    # Возвращает кортеж (id, name, created_at) или None
    return url_data


def get_url_by_name(url_name):
    """Находит URL в базе данных по его имени (нормализованному)."""
    conn = get_db_connection()
    url_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE name = %s", (url_name,))
            url_data = cur.fetchone()
    finally:
        if conn:
            conn.close()
    # Возвращает кортеж (id, name, created_at) или None
    return url_data


def insert_url(url_name):
    """Добавляет новый URL в базу данных и возвращает его данные."""
    conn = get_db_connection()
    new_url_data = None
    today = date.today() # Получение текущей даты
    try:
        with conn.cursor() as cur:
            # Вставка новой записи и получение её данных через RETURNING
            cur.execute(
                "INSERT INTO urls (name, created_at) VALUES (%s, %s) RETURNING id, name, created_at",
                (url_name, today)
            )
            new_url_data = cur.fetchone()
            conn.commit() # Подтверждение транзакции
    except psycopg.Error as e:
        # Откат транзакции при ошибке (например, дубликат UNIQUE)
        conn.rollback()
        print(f"Ошибка вставки URL: {e}")
        # Возвращаем None при ошибке
    finally:
        # Гарантированное закрытие соединения
        if conn:
            conn.close()
    # Возвращает кортеж (id, name, created_at) или None при ошибке
    return new_url_data


def get_all_urls():
    """Получает все записи из таблицы urls, сортированные по ID."""
    conn = get_db_connection()
    urls_data = []
    try:
        with conn.cursor() as cur:
            # Запрос ID и имени, сортировка по убыванию ID
            cur.execute("SELECT id, name FROM urls ORDER BY id DESC;")
            urls_data = cur.fetchall() # Извлечение всех строк
    finally:
        # Гарантированное закрытие соединения
        if conn:
            conn.close()
    # Возвращает список кортежей [(id, name), ...]
    return urls_data
