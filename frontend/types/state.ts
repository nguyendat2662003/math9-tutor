// Phản chiếu ProblemState phía Python (backend/api/routes/solve.py::_public_state).
// Giữ ĐỒNG BỘ với backend/packages/core/math9_core/state.py.

export type Confidence = "high" | "partial" | "low";
export type Mode = "basic" | "exam10" | "advanced";

export interface Predicate {
  kind: string;
  args: string[];
  value?: number | null;
}

export interface Step {
  id: string;
  claim: string;
  justification: string;
  refs: string[];
  /** Đối tượng cần tô sáng trên hình khi người dùng chọn bước này. */
  highlight: string[];
  predicate: Predicate | null;
}

export interface SubProblem {
  label: string;
  statement: string;
  goal_type: string | null;
  difficulty: number;
  steps: Step[];
  answer: string | null;
}

export interface Verification {
  algebra_ok: boolean | null;
  geometry_ok: boolean | null;
  violations: { kind: string; detail: string; step_id?: string | null }[];
  cross_check: string[];
  lemmas_found: string[];
  detail: {
    geometry?: { n_configs: number; failures: string[]; unresolved?: string[]; build_errors: string[] };
    algebra?: { results?: { ok: boolean; check: Record<string, unknown> }[]; reason?: string };
  };
}

export interface Ocr {
  statement: string;
  has_figure: boolean;
  figure_note: string;
  note: string;
}

export interface ProblemState {
  /** Mã lượt giải trong Lịch sử (API trả kèm khi đã lưu) — dùng để hỏi thêm về bài này. */
  history_id?: string;
  raw_input: string;
  latex: string | null;
  ocr: Ocr | null;
  mode: Mode;
  topic: string | null;
  difficulty: number;
  router_confidence: number;
  subproblems: SubProblem[];
  figure_svg: string | null;
  figure_quality: number | null;
  hints: string[];
  verification: Verification;
  attempts: number;
  confidence: Confidence;
  tokens: { in: number; out: number };
}

export interface StageEvent {
  stage: string;
  label: string;
  from_image?: boolean;
  statement?: string;
  note?: string;
  topic?: string;
  difficulty?: number;
  subproblems?: { label: string; goal_type: string | null }[];
  attempt?: number;
  reasons?: string[];
  geometry?: boolean;
}
