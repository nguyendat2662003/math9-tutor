"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./auth/AuthProvider";

const LINKS = [
  { href: "/", label: "Giải bài" },
  { href: "/exam", label: "Luyện đề" },
  { href: "/history", label: "Lịch sử" },
];

export function Nav() {
  const path = usePathname();
  const { user, logout } = useAuth();
  return (
    <nav className="nav">
      <div className="nav__inner">
        <span className="nav__brand">Math9 Tutor</span>
        {user && LINKS.map((l) => (
          <Link key={l.href} href={l.href} className={path === l.href ? "active" : undefined}>
            {l.label}
          </Link>
        ))}
        {user && (
          <span className="nav__user">
            <span title={`@${user.username}`}>{user.display_name}</span>
            <button type="button" className="linkbtn" onClick={logout}>Đăng xuất</button>
          </span>
        )}
      </div>
    </nav>
  );
}
