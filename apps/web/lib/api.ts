// Client gọi API. Trả về ProblemState đầy đủ, không phải chuỗi text —
// frontend cần steps, figure và confidence riêng biệt để đồng bộ hình với bước giải.

import type { ProblemState, StageEvent } from "../types/state";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Mode = "basic" | "exam10" | "advanced";

export async function solveStreaming(
  text: string,
  mode: Mode,
  onStage: (e: StageEvent) => void,
  onDone: (s: ProblemState) => void,
): Promise<void> {
  const res = await fetch(`${BASE}/api/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, mode, stream: true }),
  });
  if (!res.body) throw new Error("Không nhận được luồng phản hồi");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const c of chunks) {
      const kind = c.match(/^event: (.+)$/m)?.[1];
      const data = c.match(/^data: (.+)$/m)?.[1];
      if (!kind || !data) continue;
      if (kind === "stage") onStage(JSON.parse(data));
      if (kind === "done") onDone(JSON.parse(data));
    }
  }
}
