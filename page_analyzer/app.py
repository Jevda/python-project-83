# page_analyzer/app.py

import os
from flask import Flask
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
# Это нужно сделать до обращения к переменным через os.getenv()
load_dotenv()

# Создаем экземпляр Flask-приложения
app = Flask(__name__)

# Устанавливаем секретный ключ Flask из переменной окружения
# Ключ необходим для работы сессий и защиты от CSRF-атак
# Никогда не записывайте секретный ключ прямо в код!
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Определяем маршрут для главной страницы ('/')
@app.route('/')
def index():
    # Пока просто возвращаем текстовое сообщение
    return "Flask App Works!"

# Добавим проверку, чтобы убедиться, что ключ загрузился (для отладки)
# В реальном приложении стоит предусмотреть более надежную обработку отсутствия ключа
if not app.config['SECRET_KEY']:
    raise RuntimeError("SECRET_KEY not set in .env file!")
