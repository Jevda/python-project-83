# page_analyzer/db.py

import os
import psycopg
from dotenv import load_dotenv
# datetime больше не импортируем здесь

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def get_db_connection():
    """Устанавливает соединение с базой данных PostgreSQL."""
    try:
        conn = psycopg.connect(DATABASE_URL)
        return conn
    except psycopg.Error as e:
        print(f"Ошибка подключения к базе данных: {e}")
        raise


def get_url_by_id(url_id):
    """Находит URL в базе данных по его ID."""
    conn = get_db_connection()
    url_data = None
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, created_at FROM urls WHERE id = %s", (url_id,))
            url_data = cur.fetchone()
    finally:
        if conn:
            conn.close()
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
    return url_data


def insert_url(url_name):
    """Добавляет новый URL в базу данных, полагаясь на DEFAULT для created_at."""
    conn = get_db_connection()
    new_url_data = None
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO urls (name) VALUES (%s) RETURNING id, name, created_at",
                (url_name,)
            )
            new_url_data = cur.fetchone()
            conn.commit()
    except psycopg.Error as e:
        conn.rollback()
        print(f"Ошибка вставки URL: {e}")
    finally:
        if conn:
            conn.close()
    return new_url_data


def get_all_urls():
    """Получает все URL вместе с датой и кодом ответа последней проверки."""
    conn = get_db_connection()
    urls_list = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                WITH LatestChecks AS (
                    SELECT
                        url_id,
                        created_at,
                        status_code,
                        ROW_NUMBER() OVER(PARTITION BY url_id ORDER BY created_at DESC) as rn
                    FROM url_checks
                )
                SELECT
                    u.id,
                    u.name,
                    lc.created_at as last_check_date,
                    lc.status_code as last_check_status_code
                FROM urls u
                LEFT JOIN LatestChecks lc ON u.id = lc.url_id AND lc.rn = 1
                ORDER BY u.id DESC;
                """
            )
            urls_list = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return urls_list


# === ИЗМЕНЕННАЯ ФУНКЦИЯ ===
def insert_url_check(url_id, status_code, h1=None, title=None, description=None):
    """Добавляет запись о новой проверке со всеми данными."""
    conn = get_db_connection()
    success = False
    # now = datetime.now() # Используем DEFAULT CURRENT_TIMESTAMP
    try:
        with conn.cursor() as cur:
            # Вставляем все полученные данные
            cur.execute(
                """
                INSERT INTO url_checks (url_id, status_code, h1, title, description)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (url_id, status_code, h1, title, description)
            )
            conn.commit()
            success = True
    except psycopg.Error as e:
        conn.rollback()
        print(f"Ошибка вставки проверки URL: {e}")
    finally:
        if conn:
            conn.close()
    return success
# === КОНЕЦ ИЗМЕНЕННОЙ ФУНКЦИИ ===


def get_url_checks(url_id):
    """Получает все проверки для указанного url_id, сортированные по убыванию ID."""
    conn = get_db_connection()
    checks_list = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, url_id, status_code, h1, title, description, created_at
                FROM url_checks
                WHERE url_id = %s
                ORDER BY id DESC;
                """,
                (url_id,)
            )
            checks_list = cur.fetchall()
    finally:
        if conn:
            conn.close()
    return checks_list
