FROM python:3.11-slim

# 1. Cài đặt các thư viện lõi của hệ điều hành cho Postgres
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 2. Cấu hình môi trường
ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH=/app
ENV PORT=5001

# 3. Cài đặt thư viện Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. FIX CHÍ MẠNG: Cài đặt Chromium browser và các dependencies cho Playwright
RUN playwright install --with-deps chromium

# 5. Copy toàn bộ mã nguồn vào container
COPY . /app/

EXPOSE 5001

CMD ["python", "server.py"]