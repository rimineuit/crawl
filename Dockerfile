FROM python:3.12

# Cài các gói hệ thống mà Playwright cần
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*

# Tạo thư mục app
WORKDIR /app
COPY . /app

# Cài thư viện
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Cài Playwright và trình duyệt
RUN python -m playwright install --with-deps chromium
RUN crawl4ai-setup
RUN crawl4ai-doctor 
# # Cổng mặc định Railway sẽ gán qua biến môi trường `PORT`
# ENV PORT=8000

# # Lệnh chạy FastAPI bằng uvicorn
# CMD ["uvicorn", "test_fast_api:app", "--host", "0.0.0.0", "--port", "8000"]
