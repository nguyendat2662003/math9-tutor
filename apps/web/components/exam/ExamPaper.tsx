"use client";

import { useEffect, useRef, useState } from "react";
import { MathText } from "../MathText";
import type { Answer, Exam, ExamQuestion } from "../../types/exam";

const LETTERS = ["A", "B", "C", "D"];

interface Props {
  exam: Exam;
  responses: Record<string, Answer>;
  endsAt: number;
  busy: boolean;
  onAnswer: (qid: string, a: Answer) => void;
  onSubmit: (auto: boolean) => void;
}

export function isAnswered(a: Answer | undefined): boolean {
  if (Array.isArray(a)) return a.some((x) => x !== null);
  return typeof a === "string" && a.trim() !== "";
}

export function ExamPaper({ exam, responses, endsAt, busy, onAnswer, onSubmit }: Props) {
  const answered = exam.questions.filter((q) => isAnswered(responses[q.qid])).length;
  let lastSection = "";
  let lastGroup: string | null = null;

  return (
    <div>
      <div className="paper-bar">
        <div>
          <strong>{exam.title}</strong>
          <div className="muted">{exam.questions.length} câu · {exam.total_points} điểm · {exam.minutes} phút</div>
        </div>
        <Timer endsAt={endsAt} onExpire={() => onSubmit(true)} />
        <span className="muted">Đã làm {answered}/{exam.questions.length}</span>
        <button className="btn" disabled={busy} onClick={() => onSubmit(false)}>
          {busy ? "Đang chấm…" : "Nộp bài"}
        </button>
      </div>

      {exam.warnings.length > 0 && <div className="error" style={{ marginTop: 12 }}>{exam.warnings.join(" ")}</div>}

      {exam.questions.map((q) => {
        const header = q.section !== lastSection ? <h2 className="section">{q.section}</h2> : null;
        const ctx = q.context && q.group !== lastGroup ? (
          <div className="context">
            <MathText text={q.context} />
            {q.figure_svg && <QFigure svg={q.figure_svg} />}
          </div>
        ) : null;
        lastSection = q.section;
        lastGroup = q.group;
        return (
          <div key={q.qid}>
            {header}
            {ctx}
            <QuestionCard q={q} value={responses[q.qid] ?? null} onChange={(a) => onAnswer(q.qid, a)} />
          </div>
        );
      })}

      <div className="row" style={{ marginTop: 20 }}>
        <button className="btn" disabled={busy} onClick={() => onSubmit(false)}>Nộp bài</button>
        <span className="muted">Đã làm {answered}/{exam.questions.length} câu</span>
      </div>
    </div>
  );
}

function QuestionCard({ q, value, onChange }: { q: ExamQuestion; value: Answer; onChange: (a: Answer) => void }) {
  return (
    <div className={`q ${isAnswered(value) ? "q--done" : ""}`} id={q.qid}>
      <div className="q__head">
        <strong>{q.number}</strong>
        <span className="chip chip--muted">{q.points} điểm</span>
        {q.origin === "variant" && <span className="chip chip--muted" title={q.source}>biến thể</span>}
      </div>
      <div className="q__text"><MathText text={q.statement} /></div>
      {q.figure_svg && !q.context && <QFigure svg={q.figure_svg} />}

      {q.format === "trac_nghiem" && q.options && (
        <div className="opts">
          {q.options.map((o, i) => (
            <button
              key={i} type="button"
              className={`opt ${value === LETTERS[i] ? "on" : ""}`}
              aria-pressed={value === LETTERS[i]}
              onClick={() => onChange(value === LETTERS[i] ? null : LETTERS[i])}
            >
              <b>{LETTERS[i]}.</b> <MathText text={o} />
            </button>
          ))}
        </div>
      )}

      {q.format === "dung_sai" && q.claims && (
        <div className="tf">
          {q.claims.map((c, i) => {
            const cur = Array.isArray(value) ? value[i] ?? null : null;
            const set = (v: boolean) => {
              const next = Array.isArray(value) ? [...value] : q.claims!.map(() => null);
              next[i] = cur === v ? null : v;
              onChange(next);
            };
            return (
              <div key={i} className="tf__row">
                <span>{"abcd"[i]}) <MathText text={c} /></span>
                <span className="tf__btns">
                  <button type="button" className={cur === true ? "on" : ""} onClick={() => set(true)}>Đúng</button>
                  <button type="button" className={cur === false ? "on" : ""} onClick={() => set(false)}>Sai</button>
                </span>
              </div>
            );
          })}
        </div>
      )}

      {(q.format === "tra_loi_ngan" || (q.format === "tu_luan" && q.auto)) && (
        <label className="field" style={{ marginTop: 8 }}>
          <span className="label">{q.format === "tu_luan" ? "Đáp số cuối cùng" : "Đáp án"}</span>
          <input
            type="text" value={typeof value === "string" ? value : ""}
            placeholder={q.hint ?? "Nhập đáp án"}
            onChange={(e) => onChange(e.target.value)}
          />
        </label>
      )}

      {q.format === "tu_luan" && !q.auto && (
        <>
          <textarea
            className="draft" value={typeof value === "string" ? value : ""}
            placeholder="Nháp bài làm (không bắt buộc)"
            onChange={(e) => onChange(e.target.value)}
          />
          <div className="muted">Câu chứng minh: sau khi nộp, em xem lời giải rồi tự chấm.</div>
        </>
      )}
    </div>
  );
}

/** SVG do server của mình vẽ từ dữ liệu trong repo (không phải nội dung người dùng gửi lên). */
export function QFigure({ svg }: { svg: string }) {
  return <div className="qfig" dangerouslySetInnerHTML={{ __html: svg }} />;
}

function Timer({ endsAt, onExpire }: { endsAt: number; onExpire: () => void }) {
  const [now, setNow] = useState(() => Date.now());
  const fired = useRef(false);
  const left = Math.max(0, endsAt - now);

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, []);

  useEffect(() => {
    if (left === 0 && !fired.current) {
      fired.current = true;
      onExpire();
    }
  }, [left, onExpire]);

  const s = Math.floor(left / 1000);
  const hh = Math.floor(s / 3600);
  const mm = String(Math.floor((s % 3600) / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return (
    <span className={`timer ${s < 300 ? "timer--low" : ""}`} aria-live="polite">
      {hh > 0 ? `${hh}:` : ""}{mm}:{ss}
    </span>
  );
}
