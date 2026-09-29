"use client";

import { useState } from "react";
import type { ProblemState } from "../../types/state";
import { MathText } from "../MathText";
import { ConfidenceBadge } from "./ConfidenceBadge";

const MODE_NAME: Record<string, string> = { basic: "🌱 Cơ bản", exam10: "🎯 Thi vào 10", advanced: "🚀 Nâng cao" };

interface Props {
  s: ProblemState;
  goalTypeNames: Record<string, string>;
  activeStep: string | null;
  onHoverStep: (stepId: string | null, highlight: string[]) => void;
}

/**
 * Chế độ gợi ý là MẶC ĐỊNH: che lời giải, hiện hints trước. Học sinh bấm mới mở.
 * Đây là yêu cầu sư phạm, không phải tùy chọn. Gợi ý cũng mở dần từng cái một để
 * em tự nghĩ tiếp sau mỗi gợi ý thay vì đọc hết một lượt.
 */
export function SolutionView({ s, goalTypeNames, activeStep, onHoverStep }: Props) {
  const hasHints = s.hints.length > 0;
  const [revealed, setRevealed] = useState(!hasHints);
  const [shown, setShown] = useState(1);
  const visibleHints = revealed ? s.hints.length : Math.min(shown, s.hints.length);

  return (
    <div className="card">
      <ConfidenceBadge s={s} />
      {s.ocr && (
        <details className="ocr">
          <summary>Đề đọc từ ảnh {s.ocr.note ? `— ${s.ocr.note}` : ""}</summary>
          <pre>{s.ocr.statement}</pre>
        </details>
      )}
      <div>
        {s.topic && <span className="chip">📚 {s.topic}</span>}
        <span className="chip chip--warm">{"🔥".repeat(Math.max(1, Math.min(3, s.difficulty)))} độ khó {s.difficulty}</span>
        <span className="chip chip--muted">{MODE_NAME[s.mode] ?? s.mode}</span>
      </div>

      {hasHints && (
        <>
          <div className="section-title"><span aria-hidden>💡</span> Gợi ý</div>
          <ol className="hints">
            {s.hints.slice(0, visibleHints).map((h, i) => (
              <li key={i} className="hint">
                <span className="hint__n">{i + 1}</span>
                <span><MathText text={h} /></span>
              </li>
            ))}
            {!revealed && visibleHints < s.hints.length && (
              <li className="hint hint--locked">
                <span>🔒 Còn {s.hints.length - visibleHints} gợi ý nữa — thử tự làm trước đã nhé!</span>
                <button className="btn btn--warm" type="button" onClick={() => setShown((n) => n + 1)}>
                  Mở gợi ý {visibleHints + 1}
                </button>
              </li>
            )}
          </ol>
          {!revealed && (
            <div className="reveal">
              <button className="btn btn--ghost" type="button" onClick={() => setRevealed(true)}>
                💪 Em đã thử — xem lời giải
              </button>
            </div>
          )}
        </>
      )}

      {revealed && (
        <>
          <div className="section-title"><span aria-hidden>🧩</span> Lời giải</div>
          {s.subproblems.map((sp) => (
            <div className="sub" key={sp.label}>
              <div className="sub__head">
                <span className="sub__label">{sp.label}</span>
                <h3>
                  <MathText text={sp.statement} />{" "}
                  {sp.goal_type && <span className="chip chip--muted">{goalTypeNames[sp.goal_type] ?? sp.goal_type}</span>}
                </h3>
              </div>
              <div className="steps">
                {sp.steps.map((st, i) => (
                  <div
                    key={st.id}
                    data-n={i + 1}
                    className={`step${activeStep === st.id ? " active" : ""}`}
                    onMouseEnter={() => onHoverStep(st.id, st.highlight.length ? st.highlight : st.refs)}
                    onMouseLeave={() => onHoverStep(null, [])}
                    onClick={() => onHoverStep(st.id, st.highlight.length ? st.highlight : st.refs)}
                  >
                    <div>
                      <MathText text={st.claim} />
                      {st.predicate && <span className="step__pred">✓ kiểm bằng số</span>}
                    </div>
                    {st.justification && (
                      <div className="step__why">(<MathText text={st.justification} />)</div>
                    )}
                  </div>
                ))}
              </div>
              {sp.answer && (
                <div className="answer"><span aria-hidden>🎯</span> <span><MathText text={sp.answer} /></span></div>
              )}
            </div>
          ))}
        </>
      )}

      <details>
        <summary>Chi tiết kiểm chứng · {s.tokens.in + s.tokens.out} token</summary>
        <pre>{JSON.stringify(s.verification, null, 1)}</pre>
      </details>
    </div>
  );
}
