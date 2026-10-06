"use client";

import type { Mode } from "../../types/state";
import { ImagePicker, type PickedImage } from "./ImagePicker";

const SAMPLES: { label: string; icon: string; text: string }[] = [
  {
    label: "Phương trình bậc hai",
    icon: "📈",
    text: "Cho phương trình x² − 2(m+1)x + m² + 2 = 0 (m là tham số).\na) Giải phương trình khi m = 1.\nb) Tìm m để phương trình có hai nghiệm phân biệt x₁, x₂ thỏa mãn x₁² + x₂² = 10.",
  },
  {
    label: "Hai tiếp tuyến",
    icon: "⭕",
    text: "Cho đường tròn (O) và điểm A nằm ngoài đường tròn. Kẻ hai tiếp tuyến AB, AC với đường tròn (B, C là các tiếp điểm). Gọi H là giao điểm của OA và BC. Kẻ đường kính BD của (O). Đường thẳng AD cắt (O) tại điểm thứ hai E.\na) Chứng minh tứ giác ABOC nội tiếp.\nb) Chứng minh OA vuông góc với BC tại H.\nc) Chứng minh AB² = AE·AD.",
  },
  {
    label: "Lập hệ phương trình",
    icon: "🏭",
    text: "Tháng 3, hai tổ A và B sản xuất được 520 sản phẩm. Tháng 4, tổ A tăng 15%, tổ B tăng 12% so với tháng 3, cả hai tổ sản xuất được 592 sản phẩm. Hỏi tháng 3 mỗi tổ sản xuất được bao nhiêu sản phẩm?",
  },
];

const MODES: { id: Mode; icon: string; name: string; desc: string }[] = [
  { id: "basic", icon: "🌱", name: "Cơ bản", desc: "Đúng kiến thức SGK" },
  { id: "exam10", icon: "🎯", name: "Thi vào 10", desc: "SGK + kỹ thuật làm bài thi" },
  { id: "advanced", icon: "🚀", name: "Nâng cao", desc: "Thêm phương tích, Ptolemy" },
];

interface Props {
  text: string;
  mode: Mode;
  hints: boolean;
  busy: boolean;
  image: PickedImage | null;
  onImage: (img: PickedImage | null) => void;
  onError: (msg: string) => void;
  onText: (t: string) => void;
  onMode: (m: Mode) => void;
  onHints: (h: boolean) => void;
  onSubmit: () => void;
  onCancel: () => void;
}

export function ProblemInput(p: Props) {
  const canSubmit = !p.busy && (!!p.image || p.text.trim().length >= 5);
  return (
    <div className="card">
      <div className="input-head">
        <div className="card__title" style={{ margin: 0 }}><span aria-hidden>✏️</span> Đề bài của em</div>
        <span className="muted"><span className="kbd">Ctrl</span> + <span className="kbd">Enter</span> để giải nhanh</span>
      </div>
      <textarea
        value={p.text}
        onChange={(e) => p.onText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && canSubmit) {
            e.preventDefault();
            p.onSubmit();
          }
        }}
        placeholder={p.image
          ? "Đã có ảnh đề. Có thể ghi thêm chú thích ở đây (không bắt buộc)."
          : "Dán đề bài Toán 9 vào đây (đại số hoặc hình học, nhiều ý a, b, c...), hoặc gửi ảnh đề bên dưới"}
        disabled={p.busy}
      />
      <ImagePicker image={p.image} disabled={p.busy} onChange={p.onImage} onError={p.onError} />
      <div className="samples">
        <span className="label">Chưa có đề? Thử bài mẫu:</span>
        {SAMPLES.map((s) => (
          <button key={s.label} type="button" className="sample" onClick={() => p.onText(s.text)} disabled={p.busy}>
            <span aria-hidden>{s.icon}</span> {s.label}
          </button>
        ))}
      </div>

      <div className="modes" role="radiogroup" aria-label="Mức độ lời giải">
        {MODES.map((m) => (
          <button
            key={m.id} type="button" role="radio" aria-checked={p.mode === m.id}
            className={`mode${p.mode === m.id ? " on" : ""}`}
            onClick={() => p.onMode(m.id)} disabled={p.busy}
          >
            <span className="mode__icon" aria-hidden>{m.icon}</span>
            <span>
              <span className="mode__name">{m.name}</span>
              <span className="mode__desc">{m.desc}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="actions">
        <label className="switch">
          <input type="checkbox" checked={p.hints} onChange={(e) => p.onHints(e.target.checked)} disabled={p.busy} />
          <span className="switch__track" />
          💡 Gợi ý trước, lời giải sau
        </label>
        <span className="spacer" />
        {p.busy ? (
          <button className="btn btn--ghost btn--big" type="button" onClick={p.onCancel}>Dừng lại</button>
        ) : (
          <button className="btn btn--big" type="button" onClick={p.onSubmit} disabled={!canSubmit}>
            ✨ Giải bài
          </button>
        )}
      </div>
    </div>
  );
}
