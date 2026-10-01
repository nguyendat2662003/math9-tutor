"""Điểm vào FastAPI.

    uvicorn api.main:app --reload --port 8000

Pipeline được dựng MỘT lần khi khởi động (nạp RAG, đọc .env) và dùng chung cho
mọi request; mỗi request nhận bản sao nông với callback SSE riêng.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval", "exam", "ingest", "accounts"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .routes import admin, auth, chat, exam, health, history, similar, solve, upload  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from math9_core.graph import build_pipeline
    from math9_core.llm.client import load_env

    load_env()
    from math9_accounts import db

    db.configure()
    db.init_db()
    logging.getLogger(__name__).info("Cơ sở dữ liệu tài khoản: %s", db.backend_name())
    # Giai đoạn phát triển: nạp cả sổ tay/bài mẫu chưa soát. Production đặt RAG_REQUIRE_REVIEWED=1.
    require_reviewed = os.environ.get("RAG_REQUIRE_REVIEWED", "0") == "1"
    app.state.pipeline = build_pipeline(require_reviewed=require_reviewed)
    logging.getLogger(__name__).info("Pipeline sẵn sàng (require_reviewed=%s)", require_reviewed)
    from math9_exam.index import get_index

    idx = get_index()
    logging.getLogger(__name__).info(
        "Kho đề Qdrant: %s", f"{idx.mode} · {idx.collection} · {idx.count()} bài" if idx else "tắt (chưa cấu hình)")
    yield
    from math9_core import tracing

    tracing.flush()                 # đẩy nốt trace Langfuse đang chờ trước khi tắt


app = FastAPI(title="Math9 Tutor API", version="0.1.0", lifespan=lifespan)
# Deploy tách riêng: liệt kê domain của frontend, cách nhau bởi dấu phẩy
CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip().rstrip("/") for o in CORS_ORIGINS if o.strip()],
    allow_credentials=True,          # gửi cookie phiên đăng nhập (origin phải liệt kê cụ thể, không dùng "*")
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(solve.router)
app.include_router(upload.router)
app.include_router(exam.router)
app.include_router(similar.router)
app.include_router(admin.router)
app.include_router(auth.router)
app.include_router(history.router)
app.include_router(chat.router)
