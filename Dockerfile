# Используем официальный образ Python как базовый
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директорию для базы данных (если она нужна для SQLite)
RUN mkdir -p /app/database

# Открываем порт 5000
EXPOSE 5000

# Запускаем Flask
CMD ["python", "main.py"]
