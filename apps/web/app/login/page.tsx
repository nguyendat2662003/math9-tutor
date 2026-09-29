"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login, register } from "../../lib/api";
import { useAuth } from "../../components/auth/AuthProvider";

function LoginForm() {
  const [tab, setTab] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [password2, setPassword2] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const params = useSearchParams();
  const { user, refresh } = useAuth();
  // Chỉ quay về đường dẫn nội bộ — không để ?next= dẫn sang trang web khác
  const raw = params.get("next") ?? "/";
  const next = raw.startsWith("/") && !raw.startsWith("//") ? raw : "/";

  useEffect(() => { if (user) router.replace(next); }, [user, next, router]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (tab === "register" && password !== password2) {
      setError("Hai lần nhập mật khẩu không khớp");
      return;
    }
    setBusy(true);
    try {
      if (tab === "login") await login(username, password);
      else await register(username, password, displayName);
      await refresh();
      router.replace(next);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app auth">
      <div className="card auth__card">
        <h1>Math9 Tutor</h1>
        <p className="muted">Đăng nhập để giải bài, luyện đề và xem lại lịch sử học.</p>
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === "login"} className={tab === "login" ? "active" : ""}
            onClick={() => { setTab("login"); setError(null); }}>Đăng nhập</button>
          <button role="tab" aria-selected={tab === "register"} className={tab === "register" ? "active" : ""}
            onClick={() => { setTab("register"); setError(null); }}>Tạo tài khoản</button>
        </div>
        <form onSubmit={submit} className="auth__form">
          <label className="field">
            <span className="label">Tên đăng nhập</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username"
              autoCapitalize="none" spellCheck={false} required />
            {tab === "register" && <span className="muted">3–32 ký tự: chữ thường không dấu, số, dấu chấm, gạch dưới</span>}
          </label>
          {tab === "register" && (
            <label className="field">
              <span className="label">Tên hiển thị (không bắt buộc)</span>
              <input value={displayName} onChange={(e) => setDisplayName(e.target.value)} maxLength={60} placeholder="Ví dụ: Minh Anh" />
            </label>
          )}
          <label className="field">
            <span className="label">Mật khẩu</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete={tab === "login" ? "current-password" : "new-password"} required minLength={tab === "register" ? 8 : undefined} />
          </label>
          {tab === "register" && (
            <label className="field">
              <span className="label">Nhập lại mật khẩu</span>
              <input type="password" value={password2} onChange={(e) => setPassword2(e.target.value)} autoComplete="new-password" required />
            </label>
          )}
          {error && <div className="error">{error}</div>}
          <button className="btn" disabled={busy}>
            {busy ? "Đang xử lý…" : tab === "login" ? "Đăng nhập" : "Tạo tài khoản"}
          </button>
          {tab === "login" && <p className="muted">Quên mật khẩu? Nhờ thầy cô quản trị đặt lại giúp.</p>}
          {tab === "register" && <p className="muted">Hệ thống chỉ lưu tên đăng nhập và tên hiển thị — không cần email hay số điện thoại.</p>}
        </form>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="app"><div className="card muted">Đang tải…</div></main>}>
      <LoginForm />
    </Suspense>
  );
}
