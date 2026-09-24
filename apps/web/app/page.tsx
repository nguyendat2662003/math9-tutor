"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTopics, solveStreaming } from "../lib/api";
import type { Mode, ProblemState, StageEvent } from "../types/state";
import { ProblemInput } from "../components/chat/ProblemInput";
import type { PickedImage } from "../components/chat/ImagePicker";
import { StageProgress } from "../components/chat/StageProgress";
import { SolutionView } from "../components/solution-view/SolutionView";
import { Figure } from "../components/figure/Figure";

export default function Page() {
  const [text, setText] = useState("");
  const [mode, setMode] = useState<Mode>("exam10");
  const [hints, setHints] = useState(true);
  const [busy, setBusy] = useState(false);
  const [events, setEvents] = useState<StageEvent[]>([]);
  const [result, setResult] = useState<ProblemState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [goalTypeNames, setGoalTypeNames] = useState<Record<string, string>>({});
  const [image, setImage] = useState<PickedImage | null>(null);
  const [activeStep, setActiveStep] = useState<string | null>(null);
  const [highlight, setHighlight] = useState<string[]>([]);
  const abort = useRef<AbortController | null>(null);

  useEffect(() => {
    fetchTopics().then((t) => setGoalTypeNames(t.goal_types)).catch(() => {});
  }, []);

  async function submit() {
    setBusy(true);
    setEvents([]);
    setResult(null);
    setError(null);
    setHighlight([]);
    abort.current = new AbortController();
    try {
      await solveStreaming(
        text,
        mode,
        hints,
        image?.id ?? null,
        {
          onStage: (e) => setEvents((xs) => [...xs, e]),
          onDone: (s) => setResult(s),
          onError: (m) => setError(m),
        },
        abort.current.signal,
      );
    } catch (e) {
      if ((e as Error).name !== "AbortError") setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function cancel() {
    abort.current?.abort();
    setBusy(false);
  }

  return (
    <main className="app">
      <div className="app__head">
        <h1>Math9 Tutor</h1>
        <span>Toán 9 · gợi ý từng bước · hình vẽ chính xác · lời giải được kiểm chứng bằng máy</span>
      </div>

      <ProblemInput
        text={text} mode={mode} hints={hints} busy={busy} image={image}
        onText={setText} onMode={setMode} onHints={setHints} onImage={setImage}
        onError={setError} onSubmit={submit} onCancel={cancel}
      />

      {(busy || (events.length > 0 && (!result || events.some((e) => e.stage === "retrying")))) && (
        <div style={{ marginTop: 16 }}>
          <StageProgress events={events} done={!busy} />
        </div>
      )}
      {error && <div className="error" style={{ marginTop: 16 }}>{error}</div>}

      {result && (
        <div className="grid">
          <SolutionView
            s={result}
            goalTypeNames={goalTypeNames}
            activeStep={activeStep}
            onHoverStep={(id, hl) => { setActiveStep(id); setHighlight(hl); }}
          />
          {result.figure_svg ? (
            <div>
              <Figure svg={result.figure_svg} highlight={highlight} />
              <div className="muted" style={{ marginTop: 6 }}>
                Di chuột vào một bước giải để tô sáng các điểm, đoạn liên quan.
              </div>
            </div>
          ) : (
            <div className="card muted">Bài đại số — không có hình.</div>
          )}
        </div>
      )}
    </main>
  );
}
