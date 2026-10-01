"use client";

import { useEffect, useRef, useState } from "react";
import { chatMessages, chatStream, type ChatMessage } from "../../lib/api";
import { MathText } from "../MathText";
import type { ProblemState } from "../../types/state";

/** mã bước -> đối tượng cần tô sáng (highlight, không có thì refs) — để "[bước a2]" trong câu trả lời tô được hình. */
export function stepHighlights(s: ProblemState): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const sp of s.subproblems) for (const st of sp.steps) out[st.id.toLowerCase()] = st.highlight.length ? st.highlight : st.refs;
  return out;
}

const SUGGEST = ["Vì sao bước đầu tiên lại làm như vậy?", "Còn cách giải nào khác không?", "Dạng bài này thường gặp bẫy gì?"];
const RE_STEP = /\[bước\s+([a-z]\d+)\]/gi;

interface Props {
  solveId: string;
  /** mã bước -> các đối tượng cần tô sáng trên hình */
  steps: Record<string, string[]>;
  onHighlight: (names: string[]) => void;
}

/** Đoạn chữ thường: **in đậm** (model đôi khi vẫn viết dù đã dặn) -> <strong>, còn lại qua MathText. */
function Rich({ text }: { text: string }) {
  const parts = text.split(/\*\*([^*\n]+)\*\*/g);
  return <>{parts.map((p, i) => (i % 2 ? <strong key={i}><MathText text={p} /></strong> : <MathText key={i} text={p.replace(/^#{1,4} /gm, "")} />))}</>;
}

/** Nội dung trả lời: đoạn "[bước a2]" thành nút — di chuột vào thì tô sáng bước đó trên hình. */
function Answer({ text, steps, onHighlight }: { text: string; steps: Props["steps"]; onHighlight: Props["onHighlight"] }) {
  const out: React.ReactNode[] = [];
  let last = 0;
  for (const m of text.matchAll(RE_STEP)) {
    out.push(<Rich key={last} text={text.slice(last, m.index)} />);
    const id = m[1].toLowerCase();
    out.push(
      <button key={`s${m.index}`} type="button" className="stepref" disabled={!steps[id]}
        onMouseEnter={() => onHighlight(steps[id] ?? [])} onMouseLeave={() => onHighlight([])}
        onFocus={() => onHighlight(steps[id] ?? [])} onBlur={() => onHighlight([])}>
        bước {id}
      </button>,
    );
    last = (m.index ?? 0) + m[0].length;
  }
  out.push(<Rich key={last} text={text.slice(last)} />);
  return <div className="chat__text">{out}</div>;
}

export function FollowUpChat({ solveId, steps, onHighlight }: Props) {
  const [msgs, setMsgs] = useState<ChatMessage[]>([]);
  const [remaining, setRemaining] = useState<number | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMsgs([]);
    setRemaining(null);
    // Học sinh có thể gửi câu hỏi trước khi lịch sử tải xong: khi đó KHÔNG ghi đè danh sách đang hỏi dở
    chatMessages(solveId)
      .then((r) => {
        setMsgs((cur) => (cur.length ? cur : r.messages));
        setRemaining((cur) => (cur === null ? r.remaining : cur));
      })
      .catch(() => {});
  }, [solveId]);

  useEffect(() => { if (busy) endRef.current?.scrollIntoView({ block: "nearest" }); }, [msgs, busy]);

  async function send(text: string) {
    const q = text.trim();
    if (!q || busy) return;
    setBusy(true);
    setError(null);
    setInput("");
    const stamp = new Date().toISOString();
    const qid = "q" + stamp, aid = "a" + stamp;
    setMsgs((m) => [...m, { id: qid, role: "user", content: q, created_at: stamp },
                          { id: aid, role: "assistant", content: "", created_at: stamp }]);
    // Nối vào đúng ô trả lời theo mã — không theo vị trí "cuối danh sách"
    const append = (t: string) => setMsgs((m) => m.map((x) => (x.id === aid ? { ...x, content: x.content + t } : x)));
    try {
      await chatStream(solveId, q, {
        onToken: append,
        onDone: () => setRemaining((r) => (r === null ? r : Math.max(0, r - 1))),
        onError: (msg) => setError(msg),
      });
    } catch (e) {
      setError((e as Error).message);
      // lỗi trước khi có chữ (vd hết số câu hỏi): bỏ lượt rỗng, trả câu hỏi về ô nhập
      setMsgs((m) => (m.find((x) => x.id === aid)?.content ? m : m.filter((x) => x.id !== qid && x.id !== aid)));
      setInput(q);
    } finally {
      setBusy(false);
    }
  }

  const out = remaining === 0;
  return (
    <div className="card chat">
      <div className="chat__head">
        <h3>Hỏi thêm về bài này</h3>
        {remaining !== null && <span className="muted">Còn {remaining} câu hỏi cho bài này</span>}
      </div>
      <p className="muted chat__note">
        Câu trả lời của trợ lý dựa trên lời giải ở trên nhưng <b>không được máy kiểm chứng</b> như lời giải chính —
        thấy chỗ nào lạ thì hỏi lại thầy cô nhé.
      </p>

      {msgs.length > 0 && (
        <div className="chat__list">
          {msgs.map((m) => (
            <div key={m.id} className={`chat__msg chat__msg--${m.role}`}>
              {m.role === "assistant"
                ? (m.content ? <Answer text={m.content} steps={steps} onHighlight={onHighlight} /> : <span className="muted">Đang trả lời…</span>)
                : <div className="chat__text">{m.content}</div>}
            </div>
          ))}
          <div ref={endRef} />
        </div>
      )}

      {msgs.length === 0 && !out && (
        <div className="samples">
          {SUGGEST.map((s) => <button key={s} type="button" disabled={busy} onClick={() => send(s)}>{s}</button>)}
        </div>
      )}

      {error && <div className="error" style={{ marginTop: 8 }}>{error}</div>}

      <div className="chat__input">
        <textarea
          rows={2} value={input} disabled={busy || out} maxLength={2000}
          placeholder={out ? "Đã hết số câu hỏi cho bài này" : "Em chưa hiểu chỗ nào? (Enter để gửi, Shift+Enter xuống dòng)"}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(input); } }}
        />
        <button className="btn" disabled={busy || out || !input.trim()} onClick={() => send(input)}>
          {busy ? "Đang trả lời…" : "Gửi"}
        </button>
      </div>
    </div>
  );
}
