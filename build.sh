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
# Она вызовет 'uv sync --all-extras'
make install

echo "--- Build finished ---"