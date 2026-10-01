"use client";

import { useState } from "react";
import { MathText } from "../MathText";
import { QFigure } from "./ExamPaper";
import type { Answer, Exam, ExamResult as Result, GradedItem, ItemStatus } from "../../types/exam";

const STATUS: Record<ItemStatus, { label: string; cls: string; card: string }> = {
  dung: { label: "✓ Đúng", cls: "st--ok", card: "q--ok" },
  sai: { label: "✗ Sai", cls: "st--bad", card: "q--bad" },
  mot_phan: { label: "◐ Đúng một phần", cls: "st--warn", card: "q--warn" },
  bo_trong: { label: "○ Bỏ trống", cls: "st--muted", card: "q--muted" },
  tu_cham: { label: "✍️ Tự chấm", cls: "st--warn", card: "q--warn" },
};

/** Lời động viên theo tỉ lệ điểm — khen khi tốt, khích lệ khi chưa tốt, không chê. */
function cheer(ratio: number): { icon: string; title: string; text: string; color: string } {
  if (ratio >= 0.9) return { icon: "🏆", title: "Xuất sắc!", text: "Phong độ này thì phòng thi không làm khó được em đâu.", color: "#0f9d6b" };
  if (ratio >= 0.8) return { icon: "🌟", title: "Rất tốt!", text: "Chỉ còn vài chỗ nhỏ — xem lại câu sai là chạm điểm 9, 10.", color: "#0f9d6b" };
  if (ratio >= 0.65) return { icon: "💪", title: "Khá lắm!", text: "Nền tảng vững rồi. Ôn kỹ các câu chưa đúng để bứt phá nhé.", color: "#3b82f6" };
  if (ratio >= 0.5) return { icon: "🚀", title: "Cố lên, sắp tới đích!", text: "Em đã qua nửa chặng. Đọc lời giải từng câu sai rồi làm lại đề này.", color: "#f2a516" };
  return { icon: "📚", title: "Đừng nản nhé!", text: "Ai cũng bắt đầu từ đây. Xem lời giải bên dưới, rồi thử lại — em sẽ tiến bộ nhanh thôi.", color: "#ff7a59" };
}

interface Props {
  exam: Exam;
  result: Result;
  selfMarks: Record<string, number>;
  onSelfMark: (qid: string, pts: number) => void;
  onRetry: () => void;
  onNew: () => void;
}

function shown(a: Answer, options: string[] | null): string {
  if (Array.isArray(a)) return a.map((v, i) => `${"abcd"[i]}) ${v === null ? "—" : v ? "Đúng" : "Sai"}`).join(" · ");
  if (!a || !a.trim()) return "";
  const i = "ABCD".indexOf(a);
  return options && a.length === 1 && i >= 0 ? `${a}. ${options[i]}` : a;
}

/** Mở trang Giải bài với đề điền sẵn — lời giải chi tiết do pipeline sinh và kiểm chứng. */
function solveLink(exam: Exam, qid: string): string {
  const q = exam.questions.find((x) => x.qid === qid)!;
  let text = q.context ? `${q.context}\n${q.statement}` : q.statement;
  if (q.options) text += "\n" + q.options.map((o, i) => `${"ABCD"[i]}. ${o}`).join("; ");
  if (q.claims) text += "\n" + q.claims.map((c, i) => `${"abcd"[i]}) ${c}`).join(" ");
  return `/?q=${encodeURIComponent(text)}`;
}

export function ExamResult({ exam, result, selfMarks, onSelfMark, onRetry, onNew }: Props) {
  const [onlyWrong, setOnlyWrong] = useState(false);
  const selfScore = Object.values(selfMarks).reduce((a, b) => a + b, 0);
  const pending = result.items.filter((i) => i.status === "tu_cham" && selfMarks[i.qid] === undefined).length;
  const total = Math.round((result.auto_score + selfScore) * 100) / 100;
  const items = onlyWrong ? result.items.filter((i) => i.status !== "dung") : result.items;
  const byId = Object.fromEntries(exam.questions.map((q) => [q.qid, q]));

  // Lời động viên chỉ tính trên phần đã chấm — câu chứng minh chưa tự chấm không kéo tụt tỉ lệ
  const pendingPts = result.items
    .filter((i) => i.status === "tu_cham" && selfMarks[i.qid] === undefined)
    .reduce((a, i) => a + i.points, 0);
  const graded = result.total_points - pendingPts;
  const c = cheer(graded > 0 ? total / graded : 0);
  const pct = result.total_points > 0 ? Math.min(100, Math.round((total / result.total_points) * 100)) : 0;
  const count = (st: ItemStatus) => result.items.filter((i) => i.status === st).length;

  return (
    <div>
      <div className="card score">
        <div className="ring" style={{ "--p": pct, "--c": c.color } as React.CSSProperties}>
          <div className="ring__inner">
            <div className="score__big">{total}<span>/ {result.total_points} điểm</span></div>
          </div>
        </div>
        <div className="score__body">
          <p className="score__cheer">{c.icon} {c.title}</p>
          <div className="muted" style={{ fontSize: 15 }}>{c.text}</div>
          <div className="tally">
            <span className="tally__item st--ok">✓ {count("dung")} đúng</span>
            {count("mot_phan") > 0 && <span className="tally__item st--warn">◐ {count("mot_phan")} đúng một phần</span>}
            <span className="tally__item st--bad">✗ {count("sai")} sai</span>
            {count("bo_trong") > 0 && <span className="tally__item st--muted">○ {count("bo_trong")} bỏ trống</span>}
          </div>
          <div className="muted" style={{ marginTop: 8 }}>
            Chấm tự động: {result.auto_score}/{Math.round((result.total_points - result.self_grade_points) * 100) / 100}
            {result.self_grade_points > 0 && <> · tự chấm: {selfScore}/{result.self_grade_points}</>}
          </div>
          {pending > 0 && <div className="st--warn" style={{ marginTop: 8 }}>✍️ Còn {pending} câu chứng minh chờ em tự chấm bên dưới.</div>}
        </div>
        <div className="score__actions">
          <button className="btn" onClick={onNew}>🆕 Tạo đề mới</button>
          <button className="btn btn--ghost" onClick={onRetry}>🔁 Làm lại đề này</button>
          <label className="filter"><input type="checkbox" checked={onlyWrong} onChange={(e) => setOnlyWrong(e.target.checked)} /> Chỉ xem câu chưa đúng</label>
        </div>
      </div>

      {items.map((it) => (
        <ResultItem key={it.qid} exam={exam} it={it} q={byId[it.qid]} mark={selfMarks[it.qid]} onSelfMark={onSelfMark} />
      ))}
    </div>
  );
}

function ResultItem({ exam, it, q, mark, onSelfMark }: {
  exam: Exam; it: GradedItem; q: Exam["questions"][number]; mark: number | undefined;
  onSelfMark: (qid: string, pts: number) => void;
}) {
  const st = STATUS[it.status];
  const earned = it.status === "tu_cham" ? mark : it.earned;
  return (
    <div className={`q ${st.card}`}>
      <div className="q__head">
        <strong>{q.section} · {q.number}</strong>
        <span className={`st ${st.cls}`}>{st.label}</span>
        <span className="muted">{earned ?? "?"}/{it.points} điểm</span>
      </div>
      {q.context && <div className="context context--small"><MathText text={q.context} /></div>}
      <div className="q__text"><MathText text={q.statement} /></div>
      {q.figure_svg && <QFigure svg={q.figure_svg} />}
      {q.options && <div className="muted">{q.options.map((o, i) => `${"ABCD"[i]}. ${o}`).join("  ·  ")}</div>}
      {q.claims && <div className="muted">{q.claims.map((c, i) => `${"abcd"[i]}) ${c}`).join("  ·  ")}</div>}

      <div className="res">
        {shown(it.response, q.options) && (
          <div><span className="label">Em trả lời:</span> <MathText text={shown(it.response, q.options)} /></div>
        )}
        {it.answer && <div><span className="label">Đáp án:</span> <b><MathText text={it.answer} /></b></div>}
      </div>

      {it.solution.length > 0 && (
        <details open={it.status !== "dung"}>
          <summary>📖 Lời giải</summary>
          <ol className="sol">{it.solution.map((s, i) => <li key={i}><MathText text={s} /></li>)}</ol>
        </details>
      )}

      <div className="row" style={{ marginTop: 8 }}>
        {it.solution.length === 0 && (
          <a className="linkbtn" href={solveLink(exam, it.qid)} target="_blank" rel="noopener">
            🧠 Xem lời giải chi tiết (có kiểm chứng) ↗
          </a>
        )}
        {it.status === "tu_cham" && (
          <span className="selfmark">
            <span className="muted">Tự chấm:</span>
            {[0, it.points / 2, it.points].map((p) => (
              <button key={p} type="button" className={mark === p ? "on" : ""} onClick={() => onSelfMark(it.qid, p)}>
                {p === 0 ? "Chưa làm được" : p === it.points ? "Đủ điểm" : `Một nửa (${p})`}
              </button>
            ))}
          </span>
        )}
      </div>
    </div>
  );
}
