"""Kết nối cơ sở dữ liệu.

DATABASE_URL trong .env — chuỗi kết nối PostgreSQL của Supabase (Connect → Session pooler):
    postgresql://postgres.<ref>:<mật khẩu>@aws-0-<vùng>.pooler.supabase.com:5432/postgres
Chưa đặt thì dùng SQLite `data/app.db` cho phát triển (có cảnh báo). Test dùng SQLite trong bộ nhớ.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

log = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[3]

_engine: Engine | None = None
_Session: sessionmaker | None = None


def normalize_url(url: str) -> str:
    """Supabase đưa 'postgresql://...' (hoặc 'postgres://'); SQLAlchemy cần tên driver psycopg (v3)."""
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def configure(url: str | None = None) -> Engine:
    """Tạo engine. Gọi một lần lúc khởi động (hoặc trong test với 'sqlite://')."""
    global _engine, _Session
    if url is None:
        from math9_core.llm.client import load_env

        load_env()
        url = os.environ.get("DATABASE_URL", "").strip()
        if not url:
            path = ROOT / "data" / "app.db"
            path.parent.mkdir(parents=True, exist_ok=True)
            url = f"sqlite:///{path}"
            log.warning("Chưa đặt DATABASE_URL — dùng SQLite %s (chỉ để phát triển)", path)
    url = normalize_url(url)
    kw: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kw["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            kw["poolclass"] = StaticPool          # một kết nối dùng chung, không thì mỗi kết nối một DB rỗng
    else:
        # Pooler của Supabase (nhất là chế độ transaction, cổng 6543) không giữ prepared statement giữa các lượt
        kw["connect_args"] = {"prepare_threshold": None, "connect_timeout": 15}
        kw.update(pool_size=5, max_overflow=5, pool_recycle=300)
    _engine = create_engine(url, **kw)
    _Session = sessionmaker(_engine, expire_on_commit=False)
    return _engine


def engine() -> Engine:
    return _engine or configure()


def init_db() -> None:
    """Tạo bảng nếu chưa có. (Đổi cấu trúc bảng về sau: dùng Alembic migration.)"""
    from sqlalchemy import text

    from .models import Base

    Base.metadata.create_all(engine())
    if engine().dialect.name == "postgresql":
        # Supabase tự mở API REST (PostgREST) cho mọi bảng trong schema public, ai có "anon key"
        # (vốn công khai) cũng gọi được. Bật RLS mà KHÔNG tạo policy nào = API đó bị chặn hoàn toàn.
        # Backend kết nối bằng role chủ sở hữu bảng (postgres) nên không bị RLS ảnh hưởng.
        with engine().begin() as c:
            for table in Base.metadata.tables:
                c.execute(text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))


def backend_name() -> str:
    e = engine()
    if e.dialect.name == "sqlite":
        return "sqlite"
    return "supabase" if "supabase" in (e.url.host or "") else "postgresql"


@contextmanager
def session() -> Iterator[Session]:
    """Phiên làm việc: tự commit khi xong, rollback khi lỗi."""
    if _Session is None:
        configure()
    s = _Session()
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
