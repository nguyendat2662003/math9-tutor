// Client gọi API. Trả về ProblemState đầy đủ, không phải chuỗi text —
// frontend cần steps, figure và confidence riêng biệt để đồng bộ hình với bước giải.

import type { Mode, ProblemState, StageEvent } from "../types/state";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export interface SolveHandlers {
  onStage: (e: StageEvent) => void;
  onDone: (s: ProblemState) => void;
  onError: (message: string) => void;
}

export async function uploadImage(file: File): Promise<{ image_id: string; bytes: number }> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) {
    const detail = await res.json().catch(() => null);
    throw new Error(detail?.detail ?? `Tải ảnh thất bại (${res.status})`);
  }
  return res.json();
}

export async function solveStreaming(
  text: string,
  mode: Mode,
  hints: boolean,
  imageId: string | null,
  h: SolveHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await fetch(`${BASE}/api/solve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, mode, hints, image_id: imageId, stream: true }),
    signal,
  });
  if (!res.ok) throw new Error(`API trả về ${res.status}`);
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
      if (c.startsWith(":")) continue; // keep-alive
      const kind = c.match(/^event: (.+)$/m)?.[1];
      const data = c.match(/^data: (.+)$/m)?.[1];
      if (!kind || !data) continue;
      const payload = JSON.parse(data);
      if (kind === "stage") h.onStage(payload);
      else if (kind === "done") h.onDone(payload);
      else if (kind === "error") h.onError(payload.message ?? "Lỗi không xác định");
    }
  }
}

export async function fetchTopics(): Promise<{ topics: Record<string, string>; goal_types: Record<string, string> }> {
  const res = await fetch(`${BASE}/api/topics`);
  if (!res.ok) throw new Error(`API trả về ${res.status}`);
  return res.json();
}
