"use client";

import { useState } from "react";
import type { BlueprintList, CustomSpec, ExamRequest, Level } from "../../types/exam";

const LEVELS: { id: Level; label: string }[] = [
  { id: "tron", label: "Trộn các mức" },
  { id: "de", label: "Nhận biết – thông hiểu" },
  { id: "vua", label: "Vận dụng" },
  { id: "kho", label: "Vận dụng cao" },
];

interface Props {
  info: BlueprintList | null;
  busy: boolean;
  onStart: (req: ExamRequest) => void;
}

export function ExamSetup({ info, busy, onStart }: Props) {
  const [tab, setTab] = useState<"tinh" | "tu-chon">("tinh");
  const [spec, setSpec] = useState<CustomSpec>({
    topics: ["ALG-6", "GEO-9"],
    n_trac_nghiem: 8,
    n_tra_loi_ngan: 2,
    n_tu_luan: 3,
    level: "tron",
    minutes: 60,
  });

  if (!info) return <div className="card muted">Đang tải danh sách đề…</div>;

  const toggle = (t: string) =>
    setSpec((s) => ({ ...s, topics: s.topics.includes(t) ? s.topics.filter((x) => x !== t) : [...s.topics, t] }));
  const total = spec.n_trac_nghiem + spec.n_tra_loi_ngan + spec.n_tu_luan;

  return (
    <div className="card">
      <div className="tabs" role="tablist">
        <button role="tab" aria-selected={tab === "tinh"} className={tab === "tinh" ? "active" : ""} onClick={() => setTab("tinh")}>
          Đề thi vào 10 theo tỉnh
        </button>
        <button role="tab" aria-selected={tab === "tu-chon"} className={tab === "tu-chon" ? "active" : ""} onClick={() => setTab("tu-chon")}>
          Tự chọn chuyên đề
        </button>
      </div>

      {tab === "tinh" ? (
        <>
          <p className="muted">
            Đề đúng cấu trúc và thời gian của từng tỉnh. Câu hỏi lấy từ đề thi thật, cùng các biến thể đổi số
            (đáp án tính bằng máy). Điểm từng câu là ước lượng.
          </p>
          <div className="bp-grid">
            {info.blueprints.map((b) => (
              <button key={b.id} className="bp" disabled={busy} onClick={() => onStart({ blueprint: b.id })}>
                <strong>{b.name}</strong>
                <span>{b.style}</span>
                <span className="muted">{b.n_questions} câu · {b.minutes} phút</span>
              </button>
            ))}
          </div>
        </>
      ) : (
        <div className="custom">
          <div>
            <div className="label">Chuyên đề</div>
            <div className="topic-grid">
              {Object.entries(info.topics).map(([id, name]) => (
                <label key={id} className={`topic ${spec.topics.includes(id) ? "on" : ""}`}>
                  <input type="checkbox" checked={spec.topics.includes(id)} onChange={() => toggle(id)} />
                  <span><b>{id}</b> {name}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="row">
            <Num label="Trắc nghiệm" value={spec.n_trac_nghiem} max={40} onChange={(v) => setSpec({ ...spec, n_trac_nghiem: v })} />
            <Num label="Trả lời ngắn" value={spec.n_tra_loi_ngan} max={20} onChange={(v) => setSpec({ ...spec, n_tra_loi_ngan: v })} />
            <Num label="Tự luận" value={spec.n_tu_luan} max={15} onChange={(v) => setSpec({ ...spec, n_tu_luan: v })} />
            <Num label="Thời gian (phút)" value={spec.minutes} min={5} max={180} onChange={(v) => setSpec({ ...spec, minutes: v })} />
            <label className="field">
              <span className="label">Mức độ</span>
              <select value={spec.level} onChange={(e) => setSpec({ ...spec, level: e.target.value as Level })}>
                {LEVELS.map((l) => <option key={l.id} value={l.id}>{l.label}</option>)}
              </select>
            </label>
          </div>
          <div className="row">
            <button className="btn" disabled={busy || !spec.topics.length || !total} onClick={() => onStart({ custom: spec })}>
              {busy ? "Đang tạo đề…" : `Tạo đề ${total} câu`}
            </button>
            {!spec.topics.length && <span className="muted">Chọn ít nhất một chuyên đề.</span>}
          </div>
        </div>
      )}
      <p className="muted" style={{ marginTop: 12, marginBottom: 0 }}>
        Kho: {info.bank_size} bài từ đề thi thật · {info.templates} dạng biến thể đổi số.
      </p>
    </div>
  );
}

function Num(p: { label: string; value: number; min?: number; max: number; onChange: (v: number) => void }) {
  return (
    <label className="field">
      <span className="label">{p.label}</span>
      <input
        type="number" min={p.min ?? 0} max={p.max} value={p.value}
        onChange={(e) => p.onChange(Math.max(p.min ?? 0, Math.min(p.max, Number(e.target.value) || 0)))}
      />
    </label>
  );
}
