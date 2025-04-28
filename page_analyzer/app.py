# page_analyzer/app.py

import os
import validators
import requests
from bs4 import BeautifulSoup
# Убрали 'session' из импорта flask
from flask import (Flask, render_template, url_for, request,
                   flash, redirect, get_flashed_messages, abort)
# import psycopg2 # <-- УДАЛЕНО
from dotenv import load_dotenv
from urllib.parse import urlparse

# Импорт функций работы с БД из db.py
from .db import (get_all_urls, get_url_by_name, insert_url,
                   get_url_by_id, insert_url_check, get_url_checks)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY not set in .env file!")


# Главная страница
@app.route('/')
def index():
    """Отображает главную страницу с формой добавления URL."""
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', url_input='', messages=messages)


# Маршрут для добавления URL (только POST)
@app.route('/urls', methods=['POST'])
def add_url():
    """Обрабатывает форму добавления нового URL."""
    url_input = request.form.get('url', '')
    error = validate_url(url_input)
    if error:
        flash(error, 'danger')
        messages = get_flashed_messages(with_categories=True)
        # Возвращаем шаблон с ошибкой и статусом 422
        return render_template(
            'index.html', url_input=url_input, messages=messages
        ), 422

    normalized_url = normalize_url(url_input)
    existing_url = get_url_by_name(normalized_url)
    if existing_url:
        flash('Страница уже существует', 'info')
        return redirect(url_for('show_url', id=existing_url[0]))
    else:
        new_url = insert_url(normalized_url)
        if new_url:
            flash('Страница успешно добавлена', 'success')
            return redirect(url_for('show_url', id=new_url[0]))
        else:
            flash('Произошла ошибка при добавлении URL', 'danger')
            messages = get_flashed_messages(with_categories=True)
            return render_template(
                'index.html', url_input=url_input, messages=messages
            ), 500


# Страница списка сайтов
@app.route('/urls')
def list_urls():
    """Отображает список всех добавленных URL."""
    all_urls = get_all_urls()
    messages = get_flashed_messages(with_categories=True)
    return render_template('urls_index.html', urls=all_urls, messages=messages)


# Страница конкретного URL
@app.route('/urls/<int:id>')
def show_url(id):
    """Отображает информацию о URL и историю его проверок."""
    url_data = get_url_by_id(id)
    if url_data is None:
        abort(404, description="Страница не найдена")
    checks_data = get_url_checks(id)
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'urls_show.html',
        url=url_data,
        checks=checks_data,
        messages=messages
    )


# Маршрут для запуска проверки
@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_url_check(id):
    """Выполняет проверку URL, парсит HTML и сохраняет результаты."""
    url_item = get_url_by_id(id)
    if url_item is None:
        flash('Невозможно добавить проверку: URL не найден.', 'danger')
        return redirect(url_for('list_urls'))

    url_name = url_item[1]
    try:
        response = requests.get(url_name, timeout=10)
        response.raise_for_status()
        status_code = response.status_code
        seo_data = parse_seo_data(response.text)
        insert_url_check(
            id,
            status_code,
            seo_data['h1'],
            seo_data['title'],
            seo_data['description']
        )
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при проверке URL {url_name}: {e}")
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))


# --- Вспомогательные функции ---
def validate_url(url_string):
    """Проверяет URL на корректность и длину."""
    if not url_string:
        return 'URL обязателен'
    if len(url_string) > 255:
        return 'URL превышает 255 символов'
    if not validators.url(url_string):
        return 'Некорректный URL'
    return None


def normalize_url(url_string):
    """Нормализует URL (схема + домен, нижний регистр)."""
    parsed_url = urlparse(url_string)
    return f"{parsed_url.scheme}://{parsed_url.netloc}".lower()


def parse_seo_data(html_text):
    """Парсит HTML-текст и извлекает h1, title и description."""
    soup = BeautifulSoup(html_text, 'lxml')
    h1_tag = soup.find('h1')
    h1 = (h1_tag.string.strip()
          if h1_tag and h1_tag.string else '')
    title_tag = soup.find('title')
    title = (title_tag.string.strip()
             if title_tag and title_tag.string else '')
    desc_meta = soup.find('meta', attrs={'name': 'description'})
    description = (desc_meta.get('content', '').strip()
                   if desc_meta else '')
    return {'h1': h1, 'title': title, 'description': description}
# --- Конец вспомогательных функций ---
