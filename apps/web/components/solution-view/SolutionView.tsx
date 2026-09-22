"use client";

import { useState } from "react";
import type { ProblemState } from "../../types/state";
import { MathText } from "../MathText";
import { ConfidenceBadge } from "./ConfidenceBadge";

interface Props {
  s: ProblemState;
  goalTypeNames: Record<string, string>;
  activeStep: string | null;
  onHoverStep: (stepId: string | null, highlight: string[]) => void;
}

/**
 * Chế độ gợi ý là MẶC ĐỊNH: che lời giải, hiện hints trước. Học sinh bấm mới mở.
 * Đây là yêu cầu sư phạm, không phải tùy chọn.
 */
export function SolutionView({ s, goalTypeNames, activeStep, onHoverStep }: Props) {
  const hasHints = s.hints.length > 0;
  const [revealed, setRevealed] = useState(!hasHints);

  return (
    <div className="card">
      <ConfidenceBadge s={s} />
      <div className="muted">
        <span className="chip">{s.topic}</span>
        <span className="chip chip--muted">độ khó {s.difficulty}</span>
        <span className="chip chip--muted">{s.mode}</span>
      </div>

      {hasHints && (
        <>
          <h3 style={{ margin: "14px 0 6px" }}>Gợi ý</h3>
          <ol className="hints">
            {s.hints.map((h, i) => (
              <li key={i}><MathText text={h} /></li>
            ))}
          </ol>
          {!revealed && (
            <div className="reveal">
              <button className="btn btn--ghost" type="button" onClick={() => setRevealed(true)}>
                Em đã thử — xem lời giải
              </button>
            </div>
          )}
        </>
      )}

      {revealed &&
        s.subproblems.map((sp) => (
          <div className="sub" key={sp.label}>
            <h3>
              {sp.label}) <MathText text={sp.statement} />{" "}
              {sp.goal_type && <span className="chip chip--muted">{goalTypeNames[sp.goal_type] ?? sp.goal_type}</span>}
            </h3>
            {sp.steps.map((st) => (
              <div
                key={st.id}
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
            {sp.answer && (
              <div className="answer">→ <MathText text={sp.answer} /></div>
            )}
          </div>
        ))}

      <details>
        <summary>Chi tiết kiểm chứng · {s.tokens.in + s.tokens.out} token</summary>
        <pre>{JSON.stringify(s.verification, null, 1)}</pre>
      </details>
    </div>
  );
}
