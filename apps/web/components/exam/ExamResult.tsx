"use client";

import { useState } from "react";
import { MathText } from "../MathText";
import { QFigure } from "./ExamPaper";
import type { Answer, Exam, ExamResult as Result, GradedItem, ItemStatus } from "../../types/exam";

const STATUS: Record<ItemStatus, { label: string; cls: string }> = {
  dung: { label: "Đúng", cls: "st--ok" },
  sai: { label: "Sai", cls: "st--bad" },
  mot_phan: { label: "Đúng một phần", cls: "st--warn" },
  bo_trong: { label: "Bỏ trống", cls: "st--muted" },
  tu_cham: { label: "Tự chấm", cls: "st--warn" },
};

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

  return (
    <div>
      <div className="card score">
        <div>
          <div className="score__big">{total}<span>/{result.total_points}</span></div>
          <div className="muted">
            Chấm tự động: {result.auto_score}/{Math.round((result.total_points - result.self_grade_points) * 100) / 100}
            {result.self_grade_points > 0 && <> · tự chấm: {selfScore}/{result.self_grade_points}</>}
          </div>
          {pending > 0 && <div className="st--warn" style={{ marginTop: 6 }}>Còn {pending} câu chứng minh chờ em tự chấm bên dưới.</div>}
        </div>
        <div className="row">
          <label className="muted"><input type="checkbox" checked={onlyWrong} onChange={(e) => setOnlyWrong(e.target.checked)} /> Chỉ xem câu chưa đúng</label>
          <button className="btn btn--ghost" onClick={onRetry}>Làm lại đề này</button>
          <button className="btn" onClick={onNew}>Tạo đề mới</button>
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
    <div className="q">
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
          <summary>Lời giải</summary>
          <ol className="sol">{it.solution.map((s, i) => <li key={i}><MathText text={s} /></li>)}</ol>
        </details>
      )}

      <div className="row" style={{ marginTop: 8 }}>
        {it.solution.length === 0 && (
          <a className="linkbtn" href={solveLink(exam, it.qid)} target="_blank" rel="noopener">
            Xem lời giải chi tiết (có kiểm chứng) ↗
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
