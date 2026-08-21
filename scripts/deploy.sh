#!/bin/bash

# ClnSIt Pro — Скрипт развертывания

echo "🚀 ClnSIt Pro — Развертывание"

# 1. Установка зависимостей
pip install -r server/requirements.txt

# 2. Шифрование основного кода
python scripts/encrypt_code.py server/core_code.py

# 3. Запуск сервера
cd server
python server.py
