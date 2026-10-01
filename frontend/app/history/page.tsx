"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  deleteExam, deleteSolve, examHistory, fetchTopics, solveHistory, solveHistoryDetail, solveImageUrl,
} from "../../lib/api";
import type { ExamHistoryItem, SolveHistoryDetail, SolveHistoryItem } from "../../types/auth";
import { SolutionView } from "../../components/solution-view/SolutionView";
import { Figure } from "../../components/figure/Figure";
import { FollowUpChat, stepHighlights } from "../../components/solution-view/FollowUpChat";

const CONF = { high: ["Đã kiểm chứng", "st--ok"], partial: ["Kiểm chứng một phần", "st--warn"], low: ["Chưa chắc chắn", "st--bad"] } as const;

function when(iso: string) {
  return new Date(iso).toLocaleString("vi-VN", { dateStyle: "short", timeStyle: "short" });
}

export default function HistoryPage() {
  const [tab, setTab] = useState<"solves" | "exams">("solves");
  const [solves, setSolves] = useState<SolveHistoryItem[]>([]);
  const [exams, setExams] = useState<ExamHistoryItem[]>([]);
  const [more, setMore] = useState({ solves: false, exams: false });
  const [open, setOpen] = useState<SolveHistoryDetail | null>(null);
  const [goalTypeNames, setGoalTypeNames] = useState<Record<string, string>>({});
  const [highlight, setHighlight] = useState<string[]>([]);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (which: "solves" | "exams", offset = 0) => {
    try {
      if (which === "solves") {
        const p = await solveHistory(offset);
        setSolves((xs) => (offset ? [...xs, ...p.items] : p.items));
        setMore((m) => ({ ...m, solves: p.more }));
      } else {
        const p = await examHistory(offset);
        setExams((xs) => (offset ? [...xs, ...p.items] : p.items));
        setMore((m) => ({ ...m, exams: p.more }));
      }
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load("solves");
    load("exams");
    fetchTopics().then((t) => setGoalTypeNames(t.goal_types)).catch(() => {});
  }, [load]);

  async function openSolve(id: string) {
    setHighlight([]);
    try {
      setOpen(await solveHistoryDetail(id));
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function removeSolve(id: string) {
    if (!window.confirm("Xóa bài này khỏi lịch sử?")) return;
    await deleteSolve(id).catch((e) => setError(e.message));
    setOpen(null);
    load("solves");
  }

  async function removeExam(id: string) {
    if (!window.confirm("Xóa đề này khỏi lịch sử?")) return;
    await deleteExam(id).catch((e) => setError(e.message));
    load("exams");
  }

  if (open) {
    const s = open.state;
    return (
      <main className="app">
        <div className="row" style={{ marginBottom: 12 }}>
          <button className="linkbtn" onClick={() => setOpen(null)}>← Quay lại lịch sử</button>
          <span className="muted">{when(open.created_at)}</span>
          <button className="linkbtn" style={{ marginLeft: "auto" }} onClick={() => removeSolve(open.id)}>Xóa bài này</button>
        </div>
        <div className="card">
          <div className="label">Đề bài</div>
          <div className="q__text">{open.question || s?.latex || "(đề từ ảnh)"}</div>
          {open.has_image && <img className="hist__img" src={solveImageUrl(open.id)} alt="Ảnh đề bài" />}
          <div className="row" style={{ marginTop: 8 }}>
            <Link className="linkbtn" href={`/?q=${encodeURIComponent(open.question || s?.latex || "")}`}>Giải lại bài này</Link>
          </div>
        </div>
        {open.status === "error" && <div className="error" style={{ marginTop: 12 }}>Lượt giải này bị lỗi: {open.error}</div>}
        {open.status === "running" && <div className="card muted" style={{ marginTop: 12 }}>Lượt giải này chưa hoàn tất (có thể đã bị ngắt giữa chừng).</div>}
        {s && (
          <div className="grid">
            <SolutionView s={s} goalTypeNames={goalTypeNames} activeStep={activeStep}
              onHoverStep={(id, hl) => { setActiveStep(id); setHighlight(hl); }} />
            {s.figure_svg ? <div><Figure svg={s.figure_svg} highlight={highlight} /></div>
              : <div className="card muted">Bài đại số — không có hình.</div>}
          </div>
        )}
        {s && open.status === "done" && (
          <FollowUpChat solveId={open.id} steps={stepHighlights(s)} onHighlight={setHighlight} />
        )}
      </main>
    );
  }

  return (
    <main className="app">
      <div className="app__head">
        <h1>Lịch sử học</h1>
        <span>Xem lại bài đã giải (không tốn lượt giải) và các đề đã luyện</span>
      </div>
      {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}
      <div className="card">
        <div className="tabs" role="tablist">
          <button role="tab" aria-selected={tab === "solves"} className={tab === "solves" ? "active" : ""} onClick={() => setTab("solves")}>
            Bài đã giải
          </button>
          <button role="tab" aria-selected={tab === "exams"} className={tab === "exams" ? "active" : ""} onClick={() => setTab("exams")}>
            Đề đã luyện
          </button>
        </div>

        {tab === "solves" && (
          <>
            {solves.length === 0 && <p className="muted">Chưa có bài nào. <Link href="/">Giải bài đầu tiên</Link></p>}
            <ul className="hist">
              {solves.map((x) => {
                const conf = x.confidence ? CONF[x.confidence] : null;
                return (
                  <li key={x.id}>
                    <button type="button" onClick={() => openSolve(x.id)}>
                      <span className="hist__q">{x.question || (x.has_image ? "(đề từ ảnh)" : "(trống)")}</span>
                      <span className="row hist__meta">
                        <span className="muted">{when(x.created_at)}</span>
                        {x.topic && <span className="chip chip--muted">{x.topic}</span>}
                        {x.has_image && <span className="chip chip--muted">ảnh</span>}
                        {conf && <span className={`st ${conf[1]}`}>{conf[0]}</span>}
                        {x.status === "error" && <span className="st st--bad">Lỗi</span>}
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
            {more.solves && <button className="btn btn--ghost" onClick={() => load("solves", solves.length)}>Xem thêm</button>}
          </>
        )}

        {tab === "exams" && (
          <>
            {exams.length === 0 && <p className="muted">Chưa luyện đề nào. <Link href="/exam">Tạo đề đầu tiên</Link></p>}
            <ul className="hist">
              {exams.map((x) => (
                <li key={x.id} className="hist__exam">
                  <Link href={`/exam?resume=${x.id}`}>
                    <span className="hist__q">{x.title}</span>
                    <span className="row hist__meta">
                      <span className="muted">{when(x.created_at)} · {x.n_questions} câu</span>
                      {x.submitted_at
                        ? <span className="st st--ok">{x.score ?? 0}/{x.total} điểm</span>
                        : <span className="st st--warn">Chưa nộp — làm tiếp</span>}
                    </span>
                  </Link>
                  <button type="button" className="linkbtn" onClick={() => removeExam(x.id)}>Xóa</button>
                </li>
              ))}
            </ul>
            {more.exams && <button className="btn btn--ghost" onClick={() => load("exams", exams.length)}>Xem thêm</button>}
          </>
        )}
      </div>
    </main>
  );
}
