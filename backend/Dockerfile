# Backend Math9 Tutor (FastAPI). Build từ thư mục backend/:
#   docker build -t math9-api .
#   docker run -p 8000:8000 --env-file .env math9-api
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Cài đặt dạng editable: mã đọc data/, prompts/ theo đường dẫn tương đối với mã nguồn
COPY . .
RUN pip install -e ".[kho,tracing]"

# Render/Railway/Fly đặt biến PORT; chạy cục bộ mặc định 8000
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
