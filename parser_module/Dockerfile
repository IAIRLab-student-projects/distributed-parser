# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем код проекта
COPY . /app

# Копируем файл токена в контейнер
COPY token.txt /app/token.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Указываем команду по умолчанию
CMD ["python", "api.py"]