"use client";

import type { StageEvent } from "../../types/state";

const ORDER = ["parsing", "routing", "solving", "verifying", "rendering", "hinting"] as const;
const LABEL: Record<string, string> = {
  parsing: "Đọc đề bài",
  routing: "Xác định dạng toán",
  solving: "Giải (và dựng hình nếu là bài hình)",
  verifying: "Kiểm tra lại bằng máy",
  rendering: "Vẽ hình",
  hinting: "Soạn gợi ý",
};

export function StageProgress({ events, done }: { events: StageEvent[]; done: boolean }) {
  const seen = new Set(events.map((e) => e.stage));
  const current = events[events.length - 1]?.stage;
  const routed = events.find((e) => e.stage === "routed");
  const retries = events.filter((e) => e.stage === "retrying");

  return (
    <div className="card">
      <div className="muted">{done ? "Hoàn tất" : events[events.length - 1]?.label ?? "Đang kết nối..."}</div>
      <ul className="stages">
        {ORDER.map((s) => {
          const isDone = done || (seen.has(s) && current !== s);
          const isActive = !done && current === s;
          return (
            <li key={s} className={isActive ? "active" : isDone ? "done" : ""}>
              <span className="dot" />
              {LABEL[s]}
              {s === "routing" && routed && (
                <span className="muted">
                  — {routed.topic} · {routed.subproblems?.map((sp) => `${sp.label}) ${sp.goal_type ?? "?"}`).join(", ")}
                </span>
              )}
            </li>
          );
        })}
      </ul>
      {retries.map((r, i) => (
        <div key={i} className="muted" style={{ marginTop: 8 }}>
          Lần {r.attempt}: kiểm tra chưa đạt, đang giải lại — {r.reasons?.slice(0, 2).join("; ")}
        </div>
      ))}
    </div>
  );
}
