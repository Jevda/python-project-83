# page_analyzer/app.py

import os
import validators
from flask import (Flask, render_template, url_for, request,
                   flash, redirect, get_flashed_messages, abort)
from dotenv import load_dotenv
from urllib.parse import urlparse

# Импорт функций работы с БД
from .db import (get_all_urls, get_url_by_name, insert_url,
                   get_url_by_id, insert_url_check, get_url_checks) # get_url_checks теперь будет использоваться

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


# Страница конкретного URL (ОБНОВЛЕНА)
@app.route('/urls/<int:id>')
def show_url(id):
    """Отображает информацию о URL и историю его проверок."""
    # Получаем данные URL из базы данных по ID
    url_data = get_url_by_id(id)

    # Если URL с таким ID не найден, возвращаем ошибку 404
    if url_data is None:
        abort(404, description="Страница не найдена")

    # === ДОБАВЛЕНО: Получаем список проверок для этого URL ===
    checks_data = get_url_checks(id)

    # Если найден, рендерим шаблон страницы URL, передавая данные URL и проверок
    # url_data это кортеж (id, name, created_at)
    # checks_data это список кортежей [(check_id, url_id, status, h1, ...), (...), ...]
    return render_template('urls_show.html', url=url_data, checks=checks_data)


# Маршрут для запуска проверки
@app.route('/urls/<int:id>/checks', methods=['POST'])
def add_url_check(id):
    """Добавляет запись о новой проверке для URL с указанным ID."""
    url_item = get_url_by_id(id)
    if url_item is None:
        abort(404, description="URL не найден, проверку добавить нельзя")

    success = insert_url_check(id)

    if success:
        flash('Страница успешно проверена', 'success')
    else:
        flash('Произошла ошибка при проверке страницы', 'danger')

    return redirect(url_for('show_url', id=id))
