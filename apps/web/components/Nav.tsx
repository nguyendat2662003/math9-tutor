"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Giải bài", icon: "🧠" },
  { href: "/exam", label: "Luyện đề", icon: "📝" },
];

export function Nav() {
  const path = usePathname();
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
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} className={`nav__link${path === l.href ? " active" : ""}`}>
            <span aria-hidden>{l.icon}</span> {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
