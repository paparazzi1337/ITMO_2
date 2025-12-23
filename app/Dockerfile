FROM python:3.11-bookworm

# 1. ПОЛНАЯ ОЧИСТКА: Удаляем ВСЕ возможные конфигурационные файлы apt
#    Это гарантирует, что apt будет использовать ТОЛЬКО наш sources.list
RUN rm -f /etc/apt/sources.list && rm -rf /etc/apt/sources.list.d/*

# 2. СОЗДАЁМ sources.list с нуля, используя зеркало Yandex
RUN echo "deb http://mirror.yandex.ru/debian/ bookworm main contrib non-free" > /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian/ bookworm-updates main contrib non-free" >> /etc/apt/sources.list && \
    echo "deb http://mirror.yandex.ru/debian-security bookworm-security main contrib non-free" >> /etc/apt/sources.list

# 3. Установка системных зависимостей (теперь через быстрое зеркало и без лишних запросов)
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        --timeout=100

COPY . .

ENV PYTHONPATH=/app

CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]