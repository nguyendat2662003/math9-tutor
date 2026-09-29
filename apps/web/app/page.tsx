"use client";

import { useEffect, useRef, useState } from "react";
import { fetchTopics, solveStreaming } from "../lib/api";
import type { Mode, ProblemState, StageEvent } from "../types/state";
import { ProblemInput } from "../components/chat/ProblemInput";
import type { PickedImage } from "../components/chat/ImagePicker";
import { StageProgress } from "../components/chat/StageProgress";
import { SolutionView } from "../components/solution-view/SolutionView";
import { Figure } from "../components/figure/Figure";
import { SimilarProblems } from "../components/solution-view/SimilarProblems";
import { FollowUpChat, stepHighlights } from "../components/solution-view/FollowUpChat";

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
    // Trang luyện đề mở "xem lời giải chi tiết" bằng /?q=<đề bài>
    const q = new URLSearchParams(window.location.search).get("q");
    if (q) setText(q);
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
      <section className="hero">
        <div>
          <div className="hero__hi">Chào em 👋</div>
          <h1>Hôm nay mình chinh phục bài toán nào?</h1>
          <p>Gõ đề hoặc chụp ảnh đề gửi lên — thầy AI gợi ý từng bước, vẽ hình chính xác và kiểm tra lại lời giải bằng máy.</p>
        </div>
        <div className="hero__badges">
          <span className="hero__badge">💡 Gợi ý từng bước</span>
          <span className="hero__badge">📐 Hình vẽ chính xác</span>
          <span className="hero__badge">✅ Kiểm chứng bằng máy</span>
        </div>
        <span className="hero__deco" aria-hidden>∑</span>
      </section>

      <ProblemInput
        text={text} mode={mode} hints={hints} busy={busy} image={image}
        onText={setText} onMode={setMode} onHints={setHints} onImage={setImage}
        onError={setError} onSubmit={submit} onCancel={cancel}
      />

      {(busy || (events.length > 0 && (!result || events.some((e) => e.stage === "retrying")))) && (
        <div style={{ marginTop: 16 }}>
          <StageProgress events={events} done={!busy} ok={!!result} />
        </div>
      )}
      {error && <div className="error" style={{ marginTop: 16 }}><span aria-hidden>😵</span><span>{error}</span></div>}

      {result && (
        <div className="grid">
          <SolutionView
            s={result}
            goalTypeNames={goalTypeNames}
            activeStep={activeStep}
            onHoverStep={(id, hl) => { setActiveStep(id); setHighlight(hl); }}
          />
          {result.figure_svg ? (
            <div className="figure">
              <Figure svg={result.figure_svg} highlight={highlight} />
              <div className="figure-tip">
                <span aria-hidden>👆</span> Chạm hoặc di chuột vào một bước giải để tô sáng điểm, đoạn liên quan trên hình.
              </div>
            </div>
          ) : (
            <div className="card empty-fig">
              <div className="empty-fig__icon" aria-hidden>🔢</div>
              <strong>Bài đại số</strong>
              <div className="muted">Bài này không cần hình vẽ — tập trung vào từng bước biến đổi nhé!</div>
            </div>
          )}
        </div>
      )}
      {result?.history_id && !busy && (
        <FollowUpChat solveId={result.history_id} steps={stepHighlights(result)} onHighlight={setHighlight} />
      )}
      {result && !busy && (
        <SimilarProblems
          text={result.latex || result.raw_input}
          topic={null /* không lọc cứng theo chuyên đề: bài tiếp tuyến có thể là GEO-5 hay GEO-9 */}
          onPick={(t) => { setText(t); setImage(null); setResult(null); setEvents([]); window.scrollTo({ top: 0 }); }}
        />
      )}
    </main>
  );
}
