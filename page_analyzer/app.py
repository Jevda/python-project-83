# page_analyzer/app.py

import os
import validators
import requests
from bs4 import BeautifulSoup # Добавили импорт BeautifulSoup
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
        # ... (код валидации и добавления URL остается прежним) ...
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
    # ... (код для GET запроса остается прежним) ...
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

# Маршрут для запуска проверки (ОБНОВЛЕН для парсинга)
@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_url_check(id):
    """Выполняет проверку URL, парсит HTML и сохраняет результаты."""
    url_item = get_url_by_id(id)
    if url_item is None:
        abort(404, description="URL не найден")
    url_name = url_item[1]

    h1_text = None
    title_text = None
    description_content = None
    status_code = None

    try:
        # Выполняем GET-запрос
        response = requests.get(url_name, timeout=10)
        response.raise_for_status() # Теперь проверяем на ошибки >= 400

        # Получаем код ответа
        status_code = response.status_code

        # Парсим HTML с помощью BeautifulSoup и lxml
        soup = BeautifulSoup(response.text, 'lxml')

        # Извлекаем h1 (первый найденный)
        h1_tag = soup.find('h1')
        if h1_tag and h1_tag.string:
            h1_text = h1_tag.string.strip()

        # Извлекаем title
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            title_text = title_tag.string.strip()

        # Извлекаем description из мета-тега
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        if desc_meta and desc_meta.get('content'):
            description_content = desc_meta.get('content').strip()

        # Вставляем результат проверки в базу данных
        insert_url_check(id, status_code, h1_text, title_text, description_content)
        flash('Страница успешно проверена', 'success')

    except requests.exceptions.RequestException as e:
        # Обрабатываем ошибки запроса
        print(f"Ошибка при проверке URL {url_name}: {e}")
        flash('Произошла ошибка при проверке', 'danger')
        # При ошибке запроса запись в url_checks не добавляется

    # Перенаправляем обратно на страницу деталей URL
    return redirect(url_for('show_url', id=id))
