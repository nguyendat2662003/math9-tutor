"""Băm mật khẩu (scrypt — có sẵn trong Python, không thêm thư viện) và mã phiên."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

# scrypt: tốn ~16 MB RAM và vài chục ms mỗi lần băm — đủ chậm để dò mật khẩu không kinh tế
N, R, P, DKLEN = 2**14, 8, 1, 32


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=N, r=R, p=P, dklen=DKLEN)
    return f"scrypt${N}${R}${P}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, dk_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(password.encode(), salt=base64.b64decode(salt_b64), n=int(n), r=int(r), p=int(p),
                            dklen=len(base64.b64decode(dk_b64)))
        return hmac.compare_digest(dk, base64.b64decode(dk_b64))
    except (ValueError, TypeError):
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    """Bảng phiên chỉ lưu băm: ai đọc được DB cũng không dùng lại được mã phiên."""
    return hashlib.sha256(token.encode()).hexdigest()


# Băm sẵn một mật khẩu giả: tên đăng nhập không tồn tại vẫn tốn thời gian như sai mật khẩu,
# để không ai đo thời gian phản hồi mà dò ra tên đăng nhập nào có thật.
DUMMY_HASH = hash_password("khong-ai-dung-mat-khau-nay")
