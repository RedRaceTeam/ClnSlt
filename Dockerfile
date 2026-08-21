FROM python:3.11-slim

WORKDIR /app

# Копируем только серверные зависимости и файлы
COPY server.py .
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Создаём папку для базы данных
RUN mkdir -p /app/data
ENV DB_PATH=/app/data/licenses.db

# Открываем порт
EXPOSE 5000

# Запускаем сервер
CMD ["python", "server.py"]
