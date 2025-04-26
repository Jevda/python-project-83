#!/usr/bin/env bash
# Файл: build.sh

# Немедленно выходить, если команда завершилась с ошибкой
set -o errexit

echo "--- Installing uv (Build Step) ---"
# Скачиваем и устанавливаем последнюю версию uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Добавляем директорию с uv в системный PATH для текущей сессии оболочки
source $HOME/.local/bin/env
# Выведем версию uv в лог для информации
uv --version

echo "--- Installing project dependencies using make install (Build Step) ---"
# Используем нашу команду из Makefile для установки всех зависимостей
make install

echo "--- Running database migrations (Build Step) ---"
# Выполняем SQL-скрипт для создания таблиц
# Команда psql выполнится только если make install завершится успешно (&&)
# psql подключится к базе данных, используя DATABASE_URL из переменных окружения Render
# и выполнит команды из файла database.sql
psql -a -d $DATABASE_URL -f database.sql

echo "--- Build finished ---"