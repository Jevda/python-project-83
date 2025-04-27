# page_analyzer/app.py

import os
import validators
import requests # Добавили импорт requests
from flask import (Flask, render_template, url_for, request,
                   flash, redirect, get_flashed_messages, abort)
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
        if not validators.url(url_input):
            flash('Некорректный URL', 'danger')
            messages = get_flashed_messages(with_categories=True)
            return render_template('index.html', url_input=url_input, messages=messages), 422
        if len(url_input) > 255:
            flash('URL превышает 255 символов', 'danger')
            messages = get_flashed_messages(with_categories=True)
            return render_template('index.html', url_input=url_input, messages=messages), 422
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
                messages = get_flashed_messages(with_categories=True)
                return render_template('index.html', url_input=url_input, messages=messages), 500
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', url_input=url_input, messages=messages)

# Страница списка сайтов
@app.route('/urls')
def list_urls():
    all_urls = get_all_urls()
    return render_template('urls_index.html', urls=all_urls)

# Страница конкретного URL
@app.route('/urls/<int:id>')
def show_url(id):
    url_data = get_url_by_id(id)
    if url_data is None:
        abort(404, description="Страница не найдена")
    checks_data = get_url_checks(id)
    return render_template('urls_show.html', url=url_data, checks=checks_data)

# Маршрут для запуска проверки (ОБНОВЛЕН)
@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_url_check(id):
    """Выполняет проверку доступности для URL с указанным ID,
    сохраняет код ответа и перенаправляет на страницу URL."""
    url_item = get_url_by_id(id)
    if url_item is None:
        abort(404, description="URL не найден")
    url_name = url_item[1] # url_item = (id, name, created_at)

    try:
        # Выполняем GET-запрос
        response = requests.get(url_name, timeout=10)
        # Получаем код ответа
        status_code = response.status_code
        # Вставляем результат проверки в базу данных
        insert_url_check(id, status_code)
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException as e:
        # Обрабатываем ошибки запроса
        print(f"Ошибка при проверке URL {url_name}: {e}")
        flash('Произошла ошибка при проверке', 'danger')
        # При ошибке запись в url_checks не добавляется

    # Перенаправляем обратно на страницу деталей URL
    return redirect(url_for('show_url', id=id))
