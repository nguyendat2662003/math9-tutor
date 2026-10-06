"use client";

import { useEffect, useState } from "react";
import type { DraftProblem, ProblemFormat } from "../../types/admin";

const FORMATS: { id: ProblemFormat; label: string }[] = [
  { id: "trac_nghiem", label: "Trắc nghiệm" },
  { id: "dung_sai", label: "Đúng/Sai" },
  { id: "tra_loi_ngan", label: "Trả lời ngắn" },
  { id: "tu_luan", label: "Tự luận" },
];
const STATUS = { pending: ["Chờ duyệt", "st--warn"], approved: ["Đã vào kho", "st--ok"], rejected: ["Đã loại", "st--muted"] };

interface Props {
  p: DraftProblem;
  topics: Record<string, string>;
  selected: boolean;
  busy: boolean;
  onSelect: (on: boolean) => void;
  onSave: (changes: Partial<DraftProblem>) => Promise<void>;
}

/** Một bài trong lô: xem cảnh báo, đối chiếu đoạn đáp án trích từ tài liệu, sửa rồi lưu. */
export function ProblemCard({ p, topics, selected, busy, onSelect, onSave }: Props) {
  const [d, setD] = useState<DraftProblem>(p);
  useEffect(() => setD(p), [p]);
  const dirty = JSON.stringify(d) !== JSON.stringify(p);
  const locked = p.status === "approved";
  const [label, cls] = STATUS[p.status];

  const answerText =
    d.answer == null ? "" : typeof d.answer === "string" ? d.answer : d.answer.letter;

  function save() {
    const changes: Partial<DraftProblem> = {
      statement: d.statement, lead: d.lead, format: d.format, topic: d.topic, difficulty: d.difficulty, number: d.number,
      options: d.format === "trac_nghiem" ? (d.options ?? ["", "", "", ""]) : null,
      claims: d.format === "dung_sai" ? d.claims : null,
      answer: d.format === "trac_nghiem" ? (answerText ? { letter: answerText, value: "" } : null) : answerText || null,
    };
    return onSave(changes);
  }

  return (
    <div className={`q adm ${p.status === "rejected" ? "adm--off" : ""}`}>
      <div className="q__head">
        {p.status !== "rejected" && (
          <input type="checkbox" checked={selected} onChange={(e) => onSelect(e.target.checked)} aria-label={`Chọn ${p.number}`} />
        )}
        <strong>{p.number}</strong>
        <span className={`st ${cls}`}>{label}</span>
        {p.duplicate_of && <span className="st st--bad">Trùng {p.duplicate_of}</span>}
        <span className="muted">{p.id}</span>
      </div>

      {p.warnings.length > 0 && (
        <ul className="warn">{p.warnings.map((w, i) => <li key={i}>{w}</li>)}</ul>
      )}

      {(d.lead || p.group) && (
        <label className="field">
          <span className="label">Đề chung của bài (giống nhau ở mọi ý)</span>
          <textarea rows={2} value={d.lead ?? ""} disabled={locked} onChange={(e) => setD({ ...d, lead: e.target.value || null })} />
        </label>
      )}
      <label className="field">
        <span className="label">Đề</span>
        <textarea rows={3} value={d.statement} disabled={locked} onChange={(e) => setD({ ...d, statement: e.target.value })} />
      </label>

      <div className="row adm__fields">
        <label className="field">
          <span className="label">Dạng</span>
          <select value={d.format} disabled={locked} onChange={(e) => setD({ ...d, format: e.target.value as ProblemFormat })}>
            {FORMATS.map((f) => <option key={f.id} value={f.id}>{f.label}</option>)}
          </select>
        </label>
        <label className="field">
          <span className="label">Chuyên đề</span>
          <select value={d.topic ?? ""} disabled={locked} onChange={(e) => setD({ ...d, topic: e.target.value || null })}>
            <option value="">— chọn —</option>
            {Object.entries(topics).map(([id, name]) => <option key={id} value={id}>{id} · {name.slice(0, 40)}</option>)}
          </select>
        </label>
        <label className="field">
          <span className="label">Mức độ</span>
          <select value={d.difficulty} disabled={locked} onChange={(e) => setD({ ...d, difficulty: Number(e.target.value) })}>
            <option value={1}>1 · Nhận biết</option><option value={2}>2 · Vận dụng</option><option value={3}>3 · Vận dụng cao</option>
          </select>
        </label>
      </div>

      {d.format === "trac_nghiem" && (
        <div className="opts">
          {[0, 1, 2, 3].map((i) => (
            <label key={i} className="field">
              <span className="label">Phương án {"ABCD"[i]}</span>
              <input type="text" value={d.options?.[i] ?? ""} disabled={locked}
                onChange={(e) => { const o = [...(d.options ?? ["", "", "", ""])]; o[i] = e.target.value; setD({ ...d, options: o }); }} />
            </label>
          ))}
        </div>
      )}
      {d.format === "dung_sai" && (
        <label className="field">
          <span className="label">Các ý (mỗi dòng một ý)</span>
          <textarea rows={4} value={(d.claims ?? []).join("\n")} disabled={locked}
            onChange={(e) => setD({ ...d, claims: e.target.value.split("\n") })} />
        </label>
      )}

      <div className="row adm__fields">
        <label className="field" style={{ flex: 1 }}>
          <span className="label">
            Đáp án {d.format === "trac_nghiem" ? "(chữ cái A–D)" : d.format === "dung_sai" ? "(vd: Đ - S - Đ - Đ)" : "(để trống nếu là bài chứng minh)"}
          </span>
          <input type="text" value={answerText} disabled={locked}
            onChange={(e) => setD({ ...d, answer: d.format === "trac_nghiem" ? (e.target.value ? { letter: e.target.value.toUpperCase().slice(0, 1), value: "" } : null) : e.target.value })} />
        </label>
        {p.answer_evidence && (
          <div className="evidence"><span className="label">Trích từ tài liệu:</span> {p.answer_evidence}</div>
        )}
      </div>

      {!locked && (
        <div className="row">
          <button className="btn btn--ghost" disabled={!dirty || busy} onClick={save}>Lưu thay đổi</button>
          {dirty && <span className="muted">Chưa lưu — lưu xong cảnh báo sẽ được kiểm lại.</span>}
        </div>
      )}
    </div>
  );
}
