"""Tạo tài khoản ADMIN duy nhất (người tạo tài khoản cho học sinh và quản lý kho đề).

    python tools/create_admin.py                    # tên đăng nhập "admin", mật khẩu tự sinh
    python tools/create_admin.py --username thaygiao
    python tools/create_admin.py --reset            # quên mật khẩu admin: đặt mật khẩu tự sinh mới

Mật khẩu in ra MỘT lần; lần đăng nhập đầu hệ thống bắt đổi sang mật khẩu của riêng bạn.
Chạy trên máy có .env trỏ tới CSDL (DATABASE_URL) — không có trang web nào tạo được admin.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "accounts"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from math9_accounts import db, service  # noqa: E402
from math9_accounts.models import User  # noqa: E402
from sqlalchemy import select  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--username", default="admin")
    ap.add_argument("--display-name", default="Quản trị")
    ap.add_argument("--reset", action="store_true", help="đặt lại mật khẩu cho admin đã có")
    a = ap.parse_args()

    db.configure()
    db.init_db()
    print("CSDL:", db.backend_name())

    if a.reset:
        with db.session() as s:
            name = s.scalar(select(User.username).where(User.role == "admin"))
        if not name:
            raise SystemExit("Chưa có admin — chạy lại không kèm --reset để tạo")
        pw = service.reset_password(name, None)
        print(f"Đã đặt lại mật khẩu admin '{name}'.")
    else:
        if service.admin_exists():
            raise SystemExit("Đã có tài khoản admin (hệ thống chỉ có MỘT admin). Quên mật khẩu: thêm --reset")
        pw = service.generate_password(14)
        u = service.create_user(a.username, pw, a.display_name, role="admin", must_change_password=True)
        name = u.username
        print(f"Đã tạo admin '{name}'.")
    print(f"  Tên đăng nhập: {name}")
    print(f"  Mật khẩu tạm : {pw}")
    print("  -> Đăng nhập tại /login; hệ thống sẽ bắt đổi sang mật khẩu của riêng bạn ngay lần đầu.")


if __name__ == "__main__":
    main()
