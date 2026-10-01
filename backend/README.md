# Backend

API FastAPI (`api/`) + toàn bộ engine Python (`packages/`), dữ liệu (`data/`), prompt, eval, test.
Độc lập với `frontend/` — mọi lệnh dưới đây chạy trong thư mục `backend/`.

```bash
pip install -e ".[dev,tracing,kho]"
cp .env.example .env                      # điền OPENAI_API_KEY, DATABASE_URL...
python -m uvicorn api.main:app --reload --port 8000
pytest -q
```

## Deploy (Docker)

```bash
docker build -t math9-api .
docker run -p 8000:8000 --env-file .env math9-api
```

Render / Railway / Fly.io: tạo dịch vụ Docker với Root Directory = `backend`; container lắng nghe
biến `PORT` của nền tảng. Biến môi trường cần cho production:

| Biến | Ghi chú |
|---|---|
| `OPENAI_API_KEY`, `MODEL_NAME` | model chính |
| `DATABASE_URL` | Supabase Session pooler — bắt buộc (SQLite trong container mất khi khởi động lại) |
| `CORS_ORIGINS` | domain frontend, vd. `https://math9.vercel.app` (nhiều domain cách nhau dấu phẩy) |
| `COOKIE_SECURE=1` | chạy HTTPS |
| `COOKIE_SAMESITE=none` | CHỈ khi frontend gọi thẳng backend khác tên miền (không qua proxy của Next.js) |
| `RAG_REQUIRE_REVIEWED=1` | chỉ nạp sổ tay đã soát |
| `QDRANT_URL`, `QDRANT_API_KEY`, `LANGFUSE_*` | tùy chọn |

Kiểm tra sau khi deploy: `GET /api/health`.
