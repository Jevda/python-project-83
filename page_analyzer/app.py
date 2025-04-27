# page_analyzer/app.py

import os
import validators
import requests
from bs4 import BeautifulSoup
from flask import (Flask, render_template, url_for, request,
                   flash, redirect, get_flashed_messages, abort, session)
# import psycopg2 # <-- Убедись, что этот импорт тоже удален
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
@app.route('/', methods=['GET', 'POST'])
def index():
    url_input = request.form.get('url', '')
    if request.method == 'POST':
        if not validators.url(url_input):
            flash('Некорректный URL', 'danger')
            session['validation_error'] = True
            return redirect(url_for('list_urls'))

        if len(url_input) > 255:
            flash('URL превышает 255 символов', 'danger')
            session['validation_error'] = True
            return redirect(url_for('list_urls'))

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
                session['validation_error'] = True
                return redirect(url_for('list_urls'))

    # GET запрос
    messages = get_flashed_messages(with_categories=True)
    return render_template('index.html', url_input='', messages=messages)


# Страница списка сайтов
@app.route('/urls')
def list_urls():
    validation_error_flag = session.pop('validation_error', None)
    status_code = 422 if validation_error_flag else 200
    all_urls = get_all_urls()
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'urls_index.html',
        urls=all_urls,
        messages=messages
    ), status_code


# Страница конкретного URL
@app.route('/urls/<int:id>')
def show_url(id):
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
        h1_text = (h1_tag.string.strip()
                   if h1_tag and h1_tag.string else None)
        title_tag = soup.find('title')
        title_text = (title_tag.string.strip()
                      if title_tag and title_tag.string else None)
        desc_meta = soup.find('meta', attrs={'name': 'description'})
        desc_content = (desc_meta.get('content').strip()
                        if desc_meta and desc_meta.get('content') else None)
        insert_url_check(id, status_code, h1_text, title_text, desc_content)
        flash('Страница успешно проверена', 'success')
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при проверке URL {url_name}: {e}")
        flash('Произошла ошибка при проверке', 'danger')
        # error_message = str(e) # <-- УДАЛЕНО

    # Возвращаем редирект после блока try-except
    return redirect(url_for('show_url', id=id))
