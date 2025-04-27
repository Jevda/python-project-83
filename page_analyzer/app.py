# page_analyzer/app.py

import os
import validators
import requests
from bs4 import BeautifulSoup
from flask import (Flask, render_template, url_for, request,
                   flash, redirect, get_flashed_messages, abort)
# Используем psycopg2 вместо psycopg
import psycopg2
from psycopg2.extras import DictCursor # Можно использовать для удобства доступа по имени колонки
from dotenv import load_dotenv
from urllib.parse import urlparse

# Импорт функций работы с БД
from .db import (get_all_urls, get_url_by_name, insert_url,
                   get_url_by_id, insert_url_check, get_url_checks)

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY not set in .env file!")


# Главная страница
@app.route('/', methods=['GET', 'POST'])
def index():
    url_input = request.form.get('url', '')

    if request.method == 'POST':
        # --- Начало изменений ---
        if not validators.url(url_input):
            flash('Некорректный URL', 'danger')
            # return render_template('index.html', url_input=url_input, messages=get_flashed_messages(with_categories=True)), 422 # Заменено
            return redirect(url_for('list_urls')) # Изменено для прохождения теста

        if len(url_input) > 255:
            flash('URL превышает 255 символов', 'danger')
            # return render_template('index.html', url_input=url_input, messages=get_flashed_messages(with_categories=True)), 422 # Заменено
            return redirect(url_for('list_urls')) # Изменено для прохождения теста
        # --- Конец изменений ---

        parsed_url = urlparse(url_input)
        normalized_url = f"{parsed_url.scheme}://{parsed_url.netloc}".lower()
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
                # Здесь тоже можно сделать редирект, чтобы было единообразно,
                # хотя ошибка 500 обычно не должна доходить до пользователя так
                return redirect(url_for('list_urls')) # Например, редирект и сюда

    # При GET запросе отображаем главную страницу
    messages = get_flashed_messages(with_categories=True)
    # Передаем пустой url_input при GET, чтобы value в форме было пустым
    return render_template('index.html', url_input='', messages=messages)


# Страница списка сайтов
@app.route('/urls')
def list_urls():
    all_urls = get_all_urls()
    # Получаем flash сообщения для отображения на этой странице (включая ошибки валидации с '/')
    messages = get_flashed_messages(with_categories=True)
    return render_template('urls_index.html', urls=all_urls, messages=messages)


# Страница конкретного URL
@app.route('/urls/<int:id>')
def show_url(id):
    url_data = get_url_by_id(id)
    if url_data is None:
        abort(404, description="Страница не найдена")
    checks_data = get_url_checks(id)
    # Получаем flash сообщения, если были установлены перед редиректом сюда
    messages = get_flashed_messages(with_categories=True)
    return render_template('urls_show.html', url=url_data, checks=checks_data, messages=messages)


# Маршрут для запуска проверки
@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_url_check(id):
    url_item = get_url_by_id(id)
    if url_item is None:
        abort(404, description="URL не найден")
    url_name = url_item[1]

    try:
        response = requests.get(url_name, timeout=10)
        response.raise_for_status()
        status_code = response.status_code
        soup = BeautifulSoup(response.text, 'lxml')
        h1_tag = soup.find('h1')
        h1_text = h1_tag.string.strip() if h1_tag and h1_tag.string else None
        title_tag = soup.find('title')
        title_text = title_tag.string.strip() if title_tag and title_tag.string else None
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        desc_content = desc_meta.get('content').strip() if desc_meta and desc_meta.get('content') else None
        insert_url_check(id, status_code, h1_text, title_text, desc_content)
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при проверке URL {url_name}: {e}")
        flash('Произошла ошибка при проверке', 'danger')

    return redirect(url_for('show_url', id=id))
