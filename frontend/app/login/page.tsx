"use client";

import { Suspense, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { login } from "../../lib/api";
import { useAuth } from "../../components/auth/AuthProvider";

function LoginForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
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
    setBusy(true);
    try {
      await login(username, password);
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
        <form onSubmit={submit} className="auth__form">
          <label className="field">
            <span className="label">Tên đăng nhập</span>
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username"
              autoCapitalize="none" spellCheck={false} required />
          </label>
          <label className="field">
            <span className="label">Mật khẩu</span>
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password" required />
          </label>
          {error && <div className="error">{error}</div>}
          <button className="btn" disabled={busy}>
            {busy ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
          <p className="muted">Tài khoản do thầy cô cấp. Chưa có tài khoản hoặc quên mật khẩu? Nhờ thầy cô quản trị giúp.</p>
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
