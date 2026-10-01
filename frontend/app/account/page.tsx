"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { changePassword } from "../../lib/api";
import { useAuth } from "../../components/auth/AuthProvider";

/** Đổi mật khẩu. Tài khoản do admin cấp (hoặc vừa được đặt lại) bị đưa tới đây trước khi dùng được app. */
export default function AccountPage() {
  const { user, refresh } = useAuth();
  const router = useRouter();
  const [oldPw, setOldPw] = useState("");
  const [pw, setPw] = useState("");
  const [pw2, setPw2] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);
  const forced = !!user?.must_change_password;

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (pw !== pw2) return setError("Hai lần nhập mật khẩu mới không khớp");
    if (pw.length < 8) return setError("Mật khẩu mới cần ít nhất 8 ký tự");
    setBusy(true);
    try {
      await changePassword(oldPw, pw);
      await refresh();
      setDone(true);
      setOldPw(""); setPw(""); setPw2("");
      if (forced) router.replace("/");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  if (!user) return null;
  return (
    <main className="app auth">
      <div className="card auth__card">
        <h1>{forced ? "Đặt mật khẩu của riêng em" : "Tài khoản"}</h1>
        <p className="muted">
          {forced
            ? "Mật khẩu hiện tại do thầy cô cấp. Em đổi sang mật khẩu chỉ em biết để bắt đầu dùng Math9 Tutor nhé."
            : <>Tên đăng nhập: <b>{user.username}</b> · {user.display_name}</>}
        </p>
        <form onSubmit={submit} className="auth__form">
          <label className="field">
            <span className="label">{forced ? "Mật khẩu thầy cô cấp" : "Mật khẩu hiện tại"}</span>
            <input type="password" value={oldPw} onChange={(e) => setOldPw(e.target.value)} autoComplete="current-password" required />
          </label>
          <label className="field">
            <span className="label">Mật khẩu mới (ít nhất 8 ký tự)</span>
            <input type="password" value={pw} onChange={(e) => setPw(e.target.value)} autoComplete="new-password" required minLength={8} />
          </label>
          <label className="field">
            <span className="label">Nhập lại mật khẩu mới</span>
            <input type="password" value={pw2} onChange={(e) => setPw2(e.target.value)} autoComplete="new-password" required />
          </label>
          {error && <div className="error">{error}</div>}
          {done && !forced && <div className="okmsg">Đã đổi mật khẩu. Các máy khác đang đăng nhập tài khoản này đã bị đăng xuất.</div>}
          <button className="btn" disabled={busy}>{busy ? "Đang lưu…" : "Đổi mật khẩu"}</button>
        </form>
      </div>
    </main>
  );
}
