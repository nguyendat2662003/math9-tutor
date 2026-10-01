"""Bảng dữ liệu. Chỉ lưu thông tin tối thiểu về học sinh (phần lớn dưới 16 tuổi): không email,
không số điện thoại — tên đăng nhập, tên hiển thị, mật khẩu đã băm."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, false, true
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

Json = JSON().with_variant(JSONB(), "postgresql")


def now() -> datetime:
    return datetime.now(UTC)


def new_id() -> str:
    return uuid.uuid4().hex


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(60))
    password_hash: Mapped[str] = mapped_column(String(200))
    # Chỉ MỘT admin (tạo bằng tools/create_admin.py); học sinh do admin tạo, không tự đăng ký
    role: Mapped[str] = mapped_column(String(10), default="student", server_default="student")
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    # Mật khẩu do admin đặt thì admin biết — học sinh phải đổi ở lần đăng nhập đầu
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Chống dò mật khẩu: sai nhiều lần liên tiếp thì khóa tạm
    failed_logins: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AuthSession(Base):
    """Phiên đăng nhập. Chỉ lưu BĂM của mã phiên — lộ bảng này không đăng nhập được."""

    __tablename__ = "auth_sessions"

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class SolveRecord(Base):
    """Một lượt giải bài: đề + toàn bộ kết quả (lời giải, gợi ý, hình) để mở lại không tốn lượt gọi model."""

    __tablename__ = "solve_records"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    status: Mapped[str] = mapped_column(String(10), default="running")      # running | done | error
    question: Mapped[str] = mapped_column(Text, default="")
    image_file: Mapped[str | None] = mapped_column(String(80))              # data/user_images/<tên file>
    mode: Mapped[str] = mapped_column(String(16), default="exam10")
    topic: Mapped[str | None] = mapped_column(String(16))
    confidence: Mapped[str | None] = mapped_column(String(10))
    error: Mapped[str | None] = mapped_column(Text)
    state: Mapped[dict[str, Any] | None] = mapped_column(Json)


class ChatMessage(Base):
    """Một lượt hỏi-đáp về một bài đã giải. Xóa bài giải thì xóa luôn hỏi-đáp của bài đó."""

    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    solve_id: Mapped[str] = mapped_column(ForeignKey("solve_records.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    role: Mapped[str] = mapped_column(String(10))                            # user | assistant
    content: Mapped[str] = mapped_column(Text)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)


class ExamAttempt(Base):
    """Một đề luyện. Giữ nguyên đề (kèm đáp án — chỉ server đọc), bài làm, kết quả chấm, điểm tự chấm."""

    __tablename__ = "exam_attempts"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)          # = Exam.id
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    title: Mapped[str] = mapped_column(String(200))
    blueprint: Mapped[str] = mapped_column(String(40))
    request: Mapped[dict[str, Any]] = mapped_column(Json)                   # để "làm lại đề này"
    exam: Mapped[dict[str, Any]] = mapped_column(Json)
    responses: Mapped[dict[str, Any] | None] = mapped_column(Json)
    result: Mapped[dict[str, Any] | None] = mapped_column(Json)
    self_marks: Mapped[dict[str, Any] | None] = mapped_column(Json)
    total: Mapped[float] = mapped_column(Float)
    score: Mapped[float | None] = mapped_column(Float)                      # chấm tự động + tự chấm
