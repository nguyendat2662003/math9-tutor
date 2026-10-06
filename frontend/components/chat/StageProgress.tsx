"use client";

import type { StageEvent } from "../../types/state";

const ORDER = ["parsing", "routing", "solving", "verifying", "rendering", "hinting"] as const;
const LABEL: Record<string, string> = {
  parsing: "Đọc đề bài",
  routing: "Xác định dạng toán",
  solving: "Giải bài & dựng hình",
  verifying: "Kiểm tra lại bằng máy",
  rendering: "Vẽ hình",
  hinting: "Soạn gợi ý",
};
const ICON: Record<string, string> = {
  parsing: "📖",
  routing: "🧭",
  solving: "🧮",
  verifying: "🔍",
  rendering: "📐",
  hinting: "💡",
};

/** `done`: luồng đã kết thúc · `ok`: đã nhận được lời giải (luồng dừng giữa chừng thì done mà không ok). */
export function StageProgress({ events, done, ok }: { events: StageEvent[]; done: boolean; ok: boolean }) {
  const seen = new Set(events.map((e) => e.stage));
  const current = events[events.length - 1]?.stage;
  const routed = events.find((e) => e.stage === "routed");
  const parsed = events.find((e) => e.stage === "parsed");
  const fromImage = events.some((e) => e.stage === "parsing" && e.from_image);
  const retries = events.filter((e) => e.stage === "retrying");

  const reached = ORDER.reduce((n, s, i) => (seen.has(s) ? i + 1 : n), 0);
  const stopped = done && !ok;
  const pct = done && ok ? 100 : Math.max(6, Math.round(((reached - 0.5) / ORDER.length) * 100));
  const activeIcon = current && ICON[current] ? ICON[current] : "🤔";

  return (
    <div className="card">
      <div className="stage-head">
        <span className={`stage-head__emoji${done ? "" : " stage-head__emoji--spin"}`} aria-hidden>
          {stopped ? "🛑" : done ? "🎉" : activeIcon}
        </span>
        <div>
          <strong>{stopped ? "Đã dừng" : done ? "Xong rồi!" : "Thầy AI đang làm bài…"}</strong>
          <span className="muted">
            {stopped
              ? "Bài giải chưa hoàn tất — em bấm Giải bài để thử lại nhé."
              : done ? "Kéo xuống để xem kết quả nhé." : events[events.length - 1]?.label ?? "Đang kết nối..."}
          </span>
        </div>
      </div>
      <div className="progress" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className={`progress__bar${done ? "" : " progress__bar--live"}`} style={{ width: `${pct}%` }} />
      </div>
      <ul className="stages">
        {ORDER.map((s) => {
          const isDone = (done && ok) || (seen.has(s) && current !== s);
          const isActive = !done && current === s;
          return (
            <li key={s} className={isActive ? "active" : isDone ? "done" : ""}>
              <span className="dot" aria-hidden>{isDone ? "✓" : ICON[s]}</span>
              {s === "parsing" && fromImage ? "Đọc đề bài từ ảnh" : LABEL[s]}
            </li>
          );
        })}
      </ul>
      {routed && (
        <div className="stage-note">
          🧭 Dạng toán: <span className="chip">{routed.topic}</span>
          {routed.subproblems?.map((sp) => (
            <span key={sp.label} className="chip chip--muted">{sp.label}) {sp.goal_type ?? "?"}</span>
          ))}
        </div>
      )}
      {parsed?.statement && (
        <details className="ocr" open>
          <summary>Đề đọc được từ ảnh {parsed.note ? `— ${parsed.note}` : ""}</summary>
          <pre>{parsed.statement}</pre>
        </details>
      )}
      {retries.map((r, i) => (
        <div key={i} className="stage-note">
          🔁 Lần {r.attempt}: kiểm tra chưa đạt, đang giải lại — {r.reasons?.slice(0, 2).join("; ")}
        </div>
      ))}
    </div>
  );
}
