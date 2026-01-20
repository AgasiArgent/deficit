# Dockerfile для Deficit Tracker Bot

FROM python:3.11-slim

# Установить рабочую директорию
WORKDIR /app

# Установить системные зависимости для matplotlib
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Копировать requirements и установить Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копировать весь код приложения
COPY . .

# Создать директорию для базы данных
RUN mkdir -p /app/data

# Установить переменную окружения для Python
ENV PYTHONUNBUFFERED=1

# Создать entrypoint script для запуска миграций и бота
RUN echo '#!/bin/bash\n\
set -e\n\
echo "🔄 Running database migrations..."\n\
python migrate.py\n\
echo "🚀 Starting bot..."\n\
exec python src/main.py' > /entrypoint.sh && chmod +x /entrypoint.sh

# Запустить через entrypoint
ENTRYPOINT ["/entrypoint.sh"]
