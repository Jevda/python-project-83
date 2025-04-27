# page_analyzer/__init__.py

# Импортируем наш экземпляр 'app' из модуля 'app.py' в текущем пакете
from .app import app

# Определяем, что именно экспортируется из этого пакета
# Это важно для инструментов вроде Gunicorn или Flask CLI,
# чтобы они могли найти ваш 'app' по имени 'page_analyzer:app'
__all__ = ("app",)
