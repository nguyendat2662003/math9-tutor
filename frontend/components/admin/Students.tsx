"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { admin } from "../../lib/api";
import type { AdminUser, CreatedAccount } from "../../types/auth";

function when(iso: string | null) {
  return iso ? new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" }) : "—";
}

/** Quản lý tài khoản học sinh: admin là người DUY NHẤT tạo tài khoản (không có tự đăng ký). */
export function Students() {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [lines, setLines] = useState("");
  const [created, setCreated] = useState<CreatedAccount[] | null>(null);
  const [reset, setReset] = useState<{ username: string; password: string } | null>(null);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  const load = useCallback(async () => {
    try {
      setUsers(await admin<AdminUser[]>("/users"));
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }, []);
  useEffect(() => { load(); }, [load]);

  async function create() {
    setBusy(true);
    setMsg(null);
    setReset(null);
    try {
      const r = await admin<{ results: CreatedAccount[]; created: number }>("/users", {
        method: "POST", body: JSON.stringify({ lines: lines.split("\n").filter((l) => l.trim()) }),
      });
      setCreated(r.results);
      setMsg({ kind: "ok", text: `Đã tạo ${r.created} tài khoản. Mật khẩu chỉ hiện MỘT lần — in hoặc chép lại ngay.` });
      if (r.created) setLines("");
      load();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function resetPassword(u: AdminUser) {
    if (!window.confirm(`Đặt mật khẩu mới cho ${u.display_name} (@${u.username})? Em sẽ bị đăng xuất khỏi mọi máy.`)) return;
    try {
      const r = await admin<{ username: string; password: string }>(`/users/${encodeURIComponent(u.username)}/reset-password`, {
        method: "POST", body: JSON.stringify({}),
      });
      setCreated(null);
      setReset(r);
      load();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }

  async function toggle(u: AdminUser) {
    const verb = u.active ? "Khóa" : "Mở khóa";
    if (!window.confirm(`${verb} tài khoản ${u.display_name} (@${u.username})?`)) return;
    try {
      await admin(`/users/${encodeURIComponent(u.username)}/active`, { method: "POST", body: JSON.stringify({ active: !u.active }) });
      load();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }

  const shown = useMemo(() => {
    const k = q.trim().toLowerCase();
    return k ? users.filter((u) => u.username.includes(k) || u.display_name.toLowerCase().includes(k)) : users;
  }, [users, q]);
  const ok = created?.filter((c) => c.ok) ?? [];
  const students = users.filter((u) => u.role === "student");

  return (
    <div className="students">
      <div className="card">
        <h3>Tạo tài khoản học sinh</h3>
        <p className="muted">
          Mỗi dòng một học sinh: chỉ cần <b>Họ tên</b> (tên đăng nhập tự sinh, vd “Nguyễn Văn An” → <code>nguyenvanan</code>),
          hoặc <b>tên_đăng_nhập, Họ tên</b>. Mật khẩu tự sinh; lần đăng nhập đầu em sẽ phải đổi mật khẩu.
        </p>
        <textarea rows={5} value={lines} onChange={(e) => setLines(e.target.value)} disabled={busy}
          placeholder={"Nguyễn Văn An\nTrần Thị Bình\nhs.minh, Lê Minh"} />
        <div className="row" style={{ marginTop: 8 }}>
          <button className="btn" disabled={busy || !lines.trim()} onClick={create}>
            {busy ? "Đang tạo…" : `Tạo ${lines.split("\n").filter((l) => l.trim()).length || ""} tài khoản`}
          </button>
        </div>
        {msg && <div className={msg.kind === "error" ? "error" : "okmsg"} style={{ marginTop: 10 }}>{msg.text}</div>}
      </div>

      {(created || reset) && (
        <div className="card print-area">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3 style={{ margin: 0 }}>{reset ? "Mật khẩu mới" : "Tài khoản vừa tạo"}</h3>
            <span className="row no-print">
              <button className="btn btn--ghost" onClick={() => window.print()}>In danh sách</button>
              <button className="linkbtn" onClick={() => { setCreated(null); setReset(null); }}>Đóng</button>
            </span>
          </div>
          <p className="muted">Đăng nhập tại trang web Math9 Tutor. Lần đầu đăng nhập, em đổi sang mật khẩu của riêng em.</p>
          <table className="tbl">
            <thead><tr><th>Họ tên</th><th>Tên đăng nhập</th><th>Mật khẩu tạm</th></tr></thead>
            <tbody>
              {reset && (
                <tr><td>{users.find((u) => u.username === reset.username)?.display_name ?? ""}</td>
                  <td><code>{reset.username}</code></td><td><code>{reset.password}</code></td></tr>
              )}
              {ok.map((c) => (
                <tr key={c.username}><td>{c.display_name}</td><td><code>{c.username}</code></td><td><code>{c.password}</code></td></tr>
              ))}
            </tbody>
          </table>
          {created?.some((c) => !c.ok) && (
            <div className="warn no-print" style={{ marginTop: 10 }}>
              {created.filter((c) => !c.ok).map((c, i) => <div key={i}>“{c.line}”: {c.error}</div>)}
            </div>
          )}
        </div>
      )}

      <div className="card no-print">
        <div className="row" style={{ justifyContent: "space-between" }}>
          <h3 style={{ margin: 0 }}>Danh sách ({students.length} học sinh)</h3>
          <input className="search" placeholder="Tìm theo tên…" value={q} onChange={(e) => setQ(e.target.value)} />
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr><th>Họ tên</th><th>Tên đăng nhập</th><th>Trạng thái</th><th>Bài đã giải</th><th>Đăng nhập gần nhất</th><th></th></tr>
            </thead>
            <tbody>
              {shown.map((u) => (
                <tr key={u.username} className={u.active ? "" : "tbl--off"}>
                  <td>{u.display_name}{u.role === "admin" && <span className="chip" style={{ marginLeft: 6 }}>admin</span>}</td>
                  <td><code>{u.username}</code></td>
                  <td>
                    {!u.active ? <span className="st st--bad">Đã khóa</span>
                      : u.must_change_password ? <span className="st st--warn">Chưa đổi mật khẩu</span>
                      : <span className="st st--ok">Đang dùng</span>}
                  </td>
                  <td>{u.solves}</td>
                  <td className="muted">{when(u.last_login_at)}</td>
                  <td className="tbl__act">
                    {u.role !== "admin" && (
                      <>
                        <button className="linkbtn" onClick={() => resetPassword(u)}>Đặt lại mật khẩu</button>
                        <button className="linkbtn" onClick={() => toggle(u)}>{u.active ? "Khóa" : "Mở khóa"}</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
              {shown.length === 0 && <tr><td colSpan={6} className="muted">Chưa có tài khoản nào.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
