// Client gọi API. Trả về ProblemState đầy đủ, không phải chuỗi text —
// frontend cần steps, figure và confidence riêng biệt để đồng bộ hình với bước giải.
//
// Đăng nhập: phiên nằm trong cookie HttpOnly do API đặt; mọi lời gọi gửi kèm cookie
// (`credentials: "include"`). API trả 401 -> phát sự kiện "auth:expired" để AuthProvider
// đưa về trang đăng nhập.

import type { Mode, ProblemState, StageEvent } from "../types/state";
import type { Answer, BlueprintList, Exam, ExamRequest, ExamResult } from "../types/exam";
import type { SimilarItem } from "../types/admin";
import type { ExamHistoryDetail, HistoryPage, Me, SolveHistoryDetail, SolveHistoryItem, ExamHistoryItem } from "../types/auth";

export const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function call(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const res = await fetch(`${BASE}${path}`, { ...init, headers, credentials: "include" });
  if (res.status === 401 && !path.startsWith("/api/auth/")) {
    window.dispatchEvent(new Event("auth:expired"));
  }
  return res;
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail;
    throw new Error(typeof detail === "string" ? detail : Array.isArray(detail) ? detail[0]?.msg ?? `Lỗi ${res.status}` : `API trả về ${res.status}`);
  }
  return res.json();
}

const post = (path: string, body?: unknown) => call(path, { method: "POST", body: body === undefined ? undefined : JSON.stringify(body) });

// ---------- đăng nhập ----------

export async function fetchMe(): Promise<Me | null> {
  const res = await call("/api/auth/me");
  return res.status === 401 ? null : json(res);
}
export const login = async (username: string, password: string): Promise<Me> => json(await post("/api/auth/login", { username, password }));
export const logout = async (): Promise<void> => { await post("/api/auth/logout"); };
export const changePassword = async (old_password: string, new_password: string): Promise<void> => {
  await json(await post("/api/auth/change-password", { old_password, new_password }));
};

// ---------- giải bài ----------

export interface SolveHandlers {
  onStage: (e: StageEvent) => void;
  onDone: (s: ProblemState) => void;
  onError: (message: string) => void;
}

export async function uploadImage(file: File): Promise<{ image_id: string; bytes: number }> {
  const form = new FormData();
  form.append("file", file);
  return json(await call("/api/upload", { method: "POST", body: form }));
}

export async function solveStreaming(
  text: string,
  mode: Mode,
  hints: boolean,
  imageId: string | null,
  h: SolveHandlers,
  signal?: AbortSignal,
): Promise<void> {
  const res = await call("/api/solve", {
    method: "POST",
    body: JSON.stringify({ text, mode, hints, image_id: imageId, stream: true }),
    signal,
  });
  if (!res.ok) await json(res);                 // ném lỗi kèm lời giải thích của API (vd hết hạn mức)
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
  return json(await call("/api/topics"));
}

// ---------- luyện đề ----------

export const fetchBlueprints = async (): Promise<BlueprintList> => json(await call("/api/exam/blueprints"));
export const createExam = async (req: ExamRequest): Promise<Exam> => json(await post("/api/exam", req));
export const getExam = async (id: string): Promise<Exam & { started_at: string; submitted: boolean }> =>
  json(await call(`/api/exam/${encodeURIComponent(id)}`));
export const submitExam = async (id: string, responses: Record<string, Answer>): Promise<ExamResult> =>
  json(await post(`/api/exam/${encodeURIComponent(id)}/submit`, { responses }));

// ---------- bài tương tự ----------

export async function fetchSimilar(text: string, topic?: string | null): Promise<{ enabled: boolean; items: SimilarItem[] }> {
  const q = new URLSearchParams({ text: text.slice(0, 3900), k: "4" });
  if (topic) q.set("topic", topic);
  return json(await call(`/api/similar?${q}`));
}

// ---------- lịch sử ----------

export const solveHistory = async (offset = 0): Promise<HistoryPage<SolveHistoryItem>> =>
  json(await call(`/api/history/solves?offset=${offset}`));
export const solveHistoryDetail = async (id: string): Promise<SolveHistoryDetail> =>
  json(await call(`/api/history/solves/${encodeURIComponent(id)}`));
export const solveImageUrl = (id: string) => `${BASE}/api/history/solves/${encodeURIComponent(id)}/image`;
export const deleteSolve = async (id: string): Promise<void> => {
  await json(await call(`/api/history/solves/${encodeURIComponent(id)}`, { method: "DELETE" }));
};
export const examHistory = async (offset = 0): Promise<HistoryPage<ExamHistoryItem>> =>
  json(await call(`/api/history/exams?offset=${offset}`));
export const examHistoryDetail = async (id: string): Promise<ExamHistoryDetail> =>
  json(await call(`/api/history/exams/${encodeURIComponent(id)}`));
export const saveSelfMarks = async (id: string, marks: Record<string, number>): Promise<{ score: number }> =>
  json(await call(`/api/history/exams/${encodeURIComponent(id)}/self-marks`, { method: "PUT", body: JSON.stringify({ marks }) }));
export const deleteExam = async (id: string): Promise<void> => {
  await json(await call(`/api/history/exams/${encodeURIComponent(id)}`, { method: "DELETE" }));
};

// ---------- hỏi đáp sau khi giải ----------

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

export const chatMessages = async (solveId: string): Promise<{ messages: ChatMessage[]; remaining: number }> =>
  json(await call(`/api/chat/${encodeURIComponent(solveId)}`));

/** Gửi câu hỏi, nhận trả lời từng đoạn (SSE: token / done / error). */
export async function chatStream(
  solveId: string, message: string,
  h: { onToken: (t: string) => void; onDone: (id: string) => void; onError: (m: string) => void },
  signal?: AbortSignal,
): Promise<void> {
  const res = await call(`/api/chat/${encodeURIComponent(solveId)}`, { method: "POST", body: JSON.stringify({ message }), signal });
  if (!res.ok) await json(res);                 // ném lỗi kèm lời giải thích (vd hết số câu hỏi)
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
      if (c.startsWith(":")) continue;
      const kind = c.match(/^event: (.+)$/m)?.[1];
      const data = c.match(/^data: (.+)$/m)?.[1];
      if (!kind || !data) continue;
      const p = JSON.parse(data);
      if (kind === "token") h.onToken(p.t);
      else if (kind === "done") h.onDone(p.id);
      else if (kind === "error") h.onError(p.message ?? "Lỗi không xác định");
    }
  }
}

// ---------- quản trị (chỉ tài khoản admin — dùng cookie phiên như mọi trang khác) ----------

export async function admin<T>(path: string, init: RequestInit = {}): Promise<T> {
  return json(await call(`/api/admin${path}`, init));
}
