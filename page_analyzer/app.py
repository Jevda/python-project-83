# page_analyzer/app.py

import os
from flask import Flask, render_template # Добавили render_template
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

# Устанавливаем секретный ключ Flask из переменной окружения
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Определяем маршрут для главной страницы ('/')
@app.route('/')
def index():
    # Используем render_template для обработки и возврата шаблона index.html
    return render_template('index.html')

# Проверка наличия секретного ключа (остается без изменений)
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY not set in .env file!")
