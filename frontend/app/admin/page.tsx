"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { admin, fetchTopics } from "../../lib/api";
import { useAuth } from "../../components/auth/AuthProvider";
import { Students } from "../../components/admin/Students";
import type { AdminStats, Batch, BatchSummary, DraftProblem } from "../../types/admin";
import { ProblemCard } from "../../components/admin/ProblemCard";

const ACCEPT = ".pdf,.docx,.png,.jpg,.jpeg,.webp";

export default function AdminPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [tab, setTab] = useState<"students" | "bank">("students");
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [batch, setBatch] = useState<Batch | null>(null);
  const [topics, setTopics] = useState<Record<string, string>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [drag, setDrag] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchTopics().then((t) => setTopics(t.topics)).catch(() => {});
  }, []);

  const refresh = useCallback(async () => {
    if (!isAdmin) return;
    try {
      const [s, b] = await Promise.all([admin<AdminStats>("/stats"), admin<BatchSummary[]>("/batches")]);
      setStats(s);
      setBatches(b);
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }, [isAdmin]);

  useEffect(() => { refresh(); }, [refresh]);

  // Lô đang xử lý: hỏi lại mỗi 3 giây tới khi xong
  useEffect(() => {
    if (!batch || batch.status !== "processing") return;
    const t = setInterval(() => openBatch(batch.id, true), 3000);
    return () => clearInterval(t);
  }, [batch]); // eslint-disable-line react-hooks/exhaustive-deps

  async function openBatch(id: string, quiet = false) {
    try {
      const b = await admin<Batch>(`/batches/${id}`);
      setBatch(b);
      if (!quiet) setSelected(new Set());
      if (b.status !== "processing" && quiet) refresh();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    }
  }

  async function upload(file: File) {
    setBusy(true);
    setMsg(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const r = await admin<{ id: string }>("/documents", { method: "POST", body: form });
      setMsg({ kind: "ok", text: `Đã nhận "${file.name}". Đang tách bài (thường 30–90 giây)…` });
      await openBatch(r.id);
      refresh();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function save(p: DraftProblem, changes: Partial<DraftProblem>) {
    if (!batch) return;
    setBusy(true);
    try {
      const updated = await admin<DraftProblem>(`/batches/${batch.id}/problems/${p.id}`, {
        method: "PATCH", body: JSON.stringify(changes),
      });
      setBatch({ ...batch, problems: batch.problems.map((x) => (x.id === p.id ? updated : x)) });
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function act(action: "approve" | "reject" | "unpublish") {
    if (!batch || selected.size === 0) return;
    setBusy(true);
    try {
      const r = await admin<Record<string, unknown>>(`/batches/${batch.id}/${action}`, {
        method: "POST", body: JSON.stringify({ ids: [...selected] }),
      });
      const text =
        action === "approve"
          ? `Đã đưa ${r.approved} bài vào kho.` + ((r.skipped as string[]).length ? ` Bỏ qua: ${(r.skipped as string[]).join("; ")}` : "")
          : action === "reject" ? `Đã loại ${r.rejected} bài.` : `Đã gỡ ${r.unpublished} bài khỏi kho.`;
      setMsg({ kind: "ok", text });
      await openBatch(batch.id);
      refresh();
    } catch (e) {
      setMsg({ kind: "error", text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  if (!isAdmin) {
    return (
      <main className="app">
        <div className="card">Trang này chỉ dành cho tài khoản quản trị.</div>
      </main>
    );
  }

  const pending = batch?.problems.filter((p) => p.status === "pending") ?? [];
  const sel = batch?.problems.filter((p) => selected.has(p.id)) ?? [];

  return (
    <main className="app">
      <div className="app__head">
        <h1>Quản trị</h1>
        <span>Tạo tài khoản học sinh · tải đề lên và duyệt vào kho</span>
      </div>
      <div className="tabs" role="tablist" style={{ marginBottom: 12 }}>
        <button role="tab" aria-selected={tab === "students"} className={tab === "students" ? "active" : ""} onClick={() => setTab("students")}>
          Học sinh
        </button>
        <button role="tab" aria-selected={tab === "bank"} className={tab === "bank" ? "active" : ""} onClick={() => setTab("bank")}>
          Kho đề
        </button>
      </div>

      {tab === "students" && <Students />}
      {tab === "bank" && (<>

      {stats && (
        <div className="card stats">
          {stats.qdrant ? (
            <>
              <div><b>{stats.qdrant.uploads}</b><span>bài tải lên đã duyệt</span></div>
              <div><b>{stats.qdrant.total_points}</b><span>bài trên Qdrant (gồm kho có sẵn)</span></div>
              <div><b>{stats.bank_builtin}</b><span>bài kho có sẵn</span></div>
              <div className="stats__mode">
                Qdrant {stats.qdrant.mode === "cloud" ? "Cloud" : "cục bộ (chưa lên Cloud)"} · <code>{stats.qdrant.collection}</code>
                {Object.keys(stats.qdrant.uploads_by_topic).length > 0 && (
                  <div className="muted">{Object.entries(stats.qdrant.uploads_by_topic).map(([t, n]) => `${t}: ${n}`).join(" · ")}</div>
                )}
              </div>
            </>
          ) : (
            <div className="error">Chưa cấu hình Qdrant — đặt QDRANT_URL + QDRANT_API_KEY trong .env rồi khởi động lại API.</div>
          )}
        </div>
      )}

      <div
        className={`pick drop ${drag ? "pick--drag" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) upload(f); }}
      >
        <div>
          <b>Kéo-thả tài liệu đề vào đây</b>
          <div className="muted">PDF, Word (.docx) hoặc ảnh chụp đề · tối đa 20 MB · nên có kèm đáp án/hướng dẫn chấm</div>
        </div>
        <button className="btn" disabled={busy || !stats?.qdrant} onClick={() => fileRef.current?.click()}>Chọn file</button>
        <input ref={fileRef} type="file" accept={ACCEPT} hidden
          onChange={(e) => { const f = e.target.files?.[0]; if (f) upload(f); e.target.value = ""; }} />
      </div>

      {msg && <div className={msg.kind === "error" ? "error" : "okmsg"} style={{ marginTop: 12 }}>{msg.text}</div>}

      <div className="adm-grid">
        <aside className="card">
          <h3>Các lô đã tải</h3>
          {batches.length === 0 && <div className="muted">Chưa có lô nào.</div>}
          <ul className="batches">
            {batches.map((b) => (
              <li key={b.id} className={batch?.id === b.id ? "on" : ""}>
                <button type="button" onClick={() => openBatch(b.id)}>
                  <b>{b.filename}</b>
                  <span className="muted">
                    {b.status === "processing" ? "Đang tách bài…" : b.status === "error" ? "Lỗi" :
                      `${b.counts.pending} chờ · ${b.counts.approved} đã duyệt · ${b.counts.rejected} loại`}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <section>
          {!batch && <div className="card muted">Chọn một lô bên trái, hoặc tải tài liệu mới lên.</div>}
          {batch?.status === "processing" && <div className="card">Đang tách bài từ <b>{batch.filename}</b>… trang tự cập nhật.</div>}
          {batch?.status === "error" && <div className="error">Không xử lý được <b>{batch.filename}</b>: {batch.error}</div>}
          {batch?.status === "ready" && (
            <>
              <div className="card adm-bar">
                <div>
                  <b>{batch.source ?? batch.filename}</b>
                  <div className="muted">{batch.problems.length} bài · {pending.length} chờ duyệt</div>
                  {batch.notes.map((n, i) => <div key={i} className="st--warn" style={{ marginTop: 4 }}>{n}</div>)}
                </div>
                <div className="row">
                  <button className="linkbtn" onClick={() => setSelected(new Set(pending.filter((p) => !p.duplicate_of).map((p) => p.id)))}>
                    Chọn mọi bài chờ duyệt
                  </button>
                  <button className="btn" disabled={busy || !sel.some((p) => p.status === "pending")} onClick={() => act("approve")}>Duyệt vào kho</button>
                  <button className="btn btn--ghost" disabled={busy || !sel.some((p) => p.status === "pending")} onClick={() => act("reject")}>Loại</button>
                  <button className="btn btn--ghost" disabled={busy || !sel.some((p) => p.status === "approved")} onClick={() => act("unpublish")}>Gỡ khỏi kho</button>
                </div>
              </div>
              {batch.problems.map((p) => (
                <ProblemCard
                  key={p.id} p={p} topics={topics} busy={busy} selected={selected.has(p.id)}
                  onSelect={(on) => setSelected((s) => { const n = new Set(s); if (on) n.add(p.id); else n.delete(p.id); return n; })}
                  onSave={(c) => save(p, c)}
                />
              ))}
            </>
          )}
        </section>
      </div>
      </>)}
    </main>
  );
}
