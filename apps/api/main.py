"""Điểm vào FastAPI.

    uvicorn apps.api.main:app --reload --port 8000

Pipeline được dựng MỘT lần khi khởi động (nạp RAG, đọc .env) và dùng chung cho
mọi request; mỗi request nhận bản sao nông với callback SSE riêng.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for pkg in ("core", "curriculum", "geometry", "verifier", "retrieval", "exam"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .routes import exam, health, solve, upload  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from math9_core.graph import build_pipeline
    from math9_core.llm.client import load_env

    load_env()
    # Giai đoạn phát triển: nạp cả sổ tay/bài mẫu chưa soát. Production đặt RAG_REQUIRE_REVIEWED=1.
    require_reviewed = os.environ.get("RAG_REQUIRE_REVIEWED", "0") == "1"
    app.state.pipeline = build_pipeline(require_reviewed=require_reviewed)
    logging.getLogger(__name__).info("Pipeline sẵn sàng (require_reviewed=%s)", require_reviewed)
    yield


app = FastAPI(title="Math9 Tutor API", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router)
app.include_router(solve.router)
app.include_router(upload.router)
app.include_router(exam.router)
