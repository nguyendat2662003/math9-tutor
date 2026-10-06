"""Tracing lên Langfuse: mỗi lượt giải là một trace, mỗi agent một span, mỗi lượt gọi LLM
một generation (prompt, kết quả, token, thời gian). Cần để biết model sai ở đâu.

Bật khi `.env` có LANGFUSE_PUBLIC_KEY + LANGFUSE_SECRET_KEY (và LANGFUSE_BASE_URL nếu không
dùng cloud mặc định). Tắt hẳn bằng LANGFUSE_TRACING=0 (test đặt sẵn).

Tracing KHÔNG BAO GIỜ được làm hỏng lượt giải: thiếu khóa, thiếu thư viện hay Langfuse
lỗi mạng đều thành no-op, pipeline chạy như cũ.
"""

from __future__ import annotations

import atexit
import logging
import os
import threading
from contextlib import contextmanager
from typing import Any, Iterator

log = logging.getLogger(__name__)

_client: Any = None
_ready = False
_lock = threading.Lock()


class _Noop:
    """Đứng thay span khi tracing tắt — mọi lời gọi đều không làm gì."""

    def update(self, **_: Any) -> "_Noop":
        return self

    def set_trace_io(self, **_: Any) -> "_Noop":
        return self


NOOP = _Noop()


def client() -> Any:
    """Langfuse client dùng chung, hoặc None khi tracing tắt."""
    global _client, _ready
    if _ready:
        return _client
    with _lock:
        if _ready:
            return _client
        _ready = True
        from .llm.client import load_env

        load_env()
        pk, sk = os.environ.get("LANGFUSE_PUBLIC_KEY"), os.environ.get("LANGFUSE_SECRET_KEY")
        if os.environ.get("LANGFUSE_TRACING", "1") == "0" or not (pk and sk):
            return None
        try:
            from langfuse import Langfuse
        except ImportError:
            log.warning("Có khóa Langfuse nhưng chưa cài thư viện: pip install -e \".[tracing]\"")
            return None
        try:
            _client = Langfuse(
                public_key=pk, secret_key=sk,
                base_url=os.environ.get("LANGFUSE_BASE_URL") or os.environ.get("LANGFUSE_HOST"),
                environment=os.environ.get("LANGFUSE_ENVIRONMENT", "development"),
            )
            atexit.register(flush)
            log.info("Langfuse tracing bật")
        except Exception as e:          # cấu hình sai không được chặn pipeline
            log.warning("Không khởi tạo được Langfuse: %s", e)
            _client = None
        return _client


def enabled() -> bool:
    return client() is not None


@contextmanager
def observe(name: str, *, kind: str = "span", **attrs: Any) -> Iterator[Any]:
    """Mở một observation làm con của observation hiện tại.

    kind: span | agent | generation | retriever | evaluator... (loại observation của Langfuse;
    giao diện hiện biểu tượng theo loại). Ngoại lệ trong khối được ghi lên Langfuse
    (level ERROR) rồi ném tiếp nguyên vẹn.
    """
    lf = client()
    if lf is None:
        yield NOOP
        return
    try:
        cm = lf.start_as_current_observation(name=name, as_type=kind, **attrs)
        obs = cm.__enter__()
    except Exception as e:
        log.debug("Langfuse bỏ qua span %s: %s", name, e)
        yield NOOP
        return
    try:
        yield obs
    except BaseException as e:
        _safe(obs.update, level="ERROR", status_message=f"{type(e).__name__}: {e}"[:500])
        cm.__exit__(type(e), e, e.__traceback__)
        raise
    else:
        cm.__exit__(None, None, None)


@contextmanager
def attributes(**attrs: Any) -> Iterator[None]:
    """Thuộc tính cấp trace (trace_name, tags, session_id...) cho observation hiện tại và mọi
    observation con mở sau đó. Phải mở SỚM — observation đã tạo trước không được gắn lại."""
    if client() is None:
        yield
        return
    try:
        from langfuse import propagate_attributes

        cm = propagate_attributes(**attrs)
        cm.__enter__()
    except Exception as e:
        log.debug("Langfuse bỏ qua thuộc tính trace: %s", e)
        yield
        return
    try:
        yield
    finally:
        _safe(cm.__exit__, None, None, None)


def trace_url() -> str | None:
    lf = client()
    if lf is None:
        return None
    try:
        return lf.get_trace_url()
    except Exception:
        return None


def flush() -> None:
    """Đẩy hết trace đang chờ. Gọi cuối các lệnh chạy một lần (CLI, eval); server tự đẩy định kỳ."""
    if _client is not None:
        _safe(_client.flush)


def _safe(fn, *a, **kw) -> None:
    try:
        fn(*a, **kw)
    except Exception as e:
        log.debug("Langfuse: %s", e)
