FROM python:3.11-bookworm

WORKDIR /app

# Копируем сначала requirements.txt
COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
        --index-url https://pypi.tuna.tsinghua.edu.cn/simple \
        --trusted-host pypi.tuna.tsinghua.edu.cn \
        --timeout=300

# Копируем ВСЕ файлы проекта
COPY . .

# Устанавливаем PYTHONPATH
ENV PYTHONPATH=/app:/common

CMD ["python", "main.py"]