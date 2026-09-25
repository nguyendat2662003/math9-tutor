"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Giải bài" },
  { href: "/exam", label: "Luyện đề" },
];

export function Nav() {
  const path = usePathname();
  return (
    <nav className="nav">
      <div className="nav__inner">
        <span className="nav__brand">Math9 Tutor</span>
        {LINKS.map((l) => (
          <Link key={l.href} href={l.href} className={path === l.href ? "active" : undefined}>
            {l.label}
          </Link>
        ))}
      </div>
    </nav>
  );
}
