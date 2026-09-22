"use client";

import type { Mode } from "../../types/state";

const SAMPLES: { label: string; text: string }[] = [
  {
    label: "Phương trình bậc hai",
    text: "Cho phương trình x² − 2(m+1)x + m² + 2 = 0 (m là tham số).\na) Giải phương trình khi m = 1.\nb) Tìm m để phương trình có hai nghiệm phân biệt x₁, x₂ thỏa mãn x₁² + x₂² = 10.",
  },
  {
    label: "Hai tiếp tuyến",
    text: "Cho đường tròn (O) và điểm A nằm ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC với đường tròn (B, C là các tiếp điểm). Gọi H là giao điểm của OA và BC. Kẻ đường kính BD của (O). Đường thẳng AD cắt (O) tại điểm thứ hai E.\na) Chứng minh tứ giác ABOC nội tiếp.\nb) Chứng minh OA vuông góc với BC tại H.\nc) Chứng minh AB² = AE·AD.",
  },
  {
    label: "Lập hệ phương trình",
    text: "Tháng 3, hai tổ A và B sản xuất được 520 sản phẩm. Tháng 4, tổ A tăng 15%, tổ B tăng 12% so với tháng 3, cả hai tổ sản xuất được 592 sản phẩm. Hỏi tháng 3 mỗi tổ sản xuất được bao nhiêu sản phẩm?",
  },
];

interface Props {
  text: string;
  mode: Mode;
  hints: boolean;
  busy: boolean;
  onText: (t: string) => void;
  onMode: (m: Mode) => void;
  onHints: (h: boolean) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export function ProblemInput(p: Props) {
  return (
    <div className="card">
      <textarea
        value={p.text}
        onChange={(e) => p.onText(e.target.value)}
        placeholder="Dán đề bài Toán 9 vào đây (đại số hoặc hình học, nhiều ý a, b, c...)"
        disabled={p.busy}
      />
      <div className="samples">
        <span className="muted">Bài mẫu:</span>
        {SAMPLES.map((s) => (
          <button key={s.label} type="button" onClick={() => p.onText(s.text)} disabled={p.busy}>
            {s.label}
          </button>
        ))}
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <select value={p.mode} onChange={(e) => p.onMode(e.target.value as Mode)} disabled={p.busy}>
          <option value="basic">Cơ bản — đúng SGK</option>
          <option value="exam10">Thi vào 10 — SGK + kỹ thuật thi</option>
          <option value="advanced">Nâng cao — thêm phương tích, Ptolemy</option>
        </select>
        <label className="muted" style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input type="checkbox" checked={p.hints} onChange={(e) => p.onHints(e.target.checked)} disabled={p.busy} />
          Gợi ý trước, lời giải sau
        </label>
        <span style={{ flex: 1 }} />
        {p.busy ? (
          <button className="btn btn--ghost" type="button" onClick={p.onCancel}>Hủy</button>
        ) : (
          <button className="btn" type="button" onClick={p.onSubmit} disabled={p.text.trim().length < 5}>
            Giải
          </button>
        )}
      </div>
    </div>
  );
}
