# Makefile

# Переменная для порта. Render.com установит её значение автоматически.
PORT ?= 8000

# Установка/синхронизация всех зависимостей (основных и dev)
# Вернули команду к исходному виду
install:
	uv sync --all-extras

# Запуск сервера для разработки Flask
dev:
	uv run flask --debug --app page_analyzer:app run

# Запуск линтера (ruff) для проверки качества кода
lint:
	uv run ruff check .

# Запуск сервера в режиме "продакшен" локально с помощью gunicorn
start:
	uv run gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

# === Команды для Render.com ===

# Команда СБОРКИ для Render.com - просто запускает скрипт build.sh
build:
	./build.sh

# Команда ЗАПУСКА для Render.com - вызывает gunicorn напрямую
render-start:
	gunicorn -w 5 -b 0.0.0.0:$(PORT) page_analyzer:app

# Объявляем цели как "phony"
.PHONY: install dev lint start build render-start