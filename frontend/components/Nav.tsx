"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./auth/AuthProvider";

const LINKS = [
  { href: "/", label: "Giải bài", icon: "🧠" },
  { href: "/exam", label: "Luyện đề", icon: "📝" },
  { href: "/history", label: "Lịch sử", icon: "🕘" },
];

export function Nav() {
  const path = usePathname();
  const { user, logout } = useAuth();
  return (
    <nav className="nav">
      <div className="nav__inner">
        <Link href="/" className="nav__brand">
          <span className="nav__logo" aria-hidden>π</span>
          <span>
            <span className="nav__name">Math9 Tutor</span>
            <span className="nav__tag">Bạn đồng hành Toán 9</span>
          </span>
        </Link>
        {user && [...LINKS, ...(user.role === "admin" ? [{ href: "/admin", label: "Quản trị", icon: "🛠️" }] : [])].map((l) => (
          <Link key={l.href} href={l.href} title={l.label} className={`nav__link${path === l.href ? " active" : ""}`}>
            <span aria-hidden>{l.icon}</span> <span className="nav__label">{l.label}</span>
          </Link>
        ))}
        {user && (
          <span className="nav__user">
            <Link href="/account" title={`@${user.username} · đổi mật khẩu`} className="nav__me">{user.display_name}</Link>
            <button type="button" className="linkbtn" onClick={logout}>Đăng xuất</button>
          </span>
        )}
      </div>
    </nav>
  );
}
