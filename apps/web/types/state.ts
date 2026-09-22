// Phản chiếu ProblemState phía Python. Giữ ĐỒNG BỘ với
// packages/core/math9_core/state.py — cân nhắc sinh tự động từ OpenAPI schema.

export type Confidence = "high" | "partial" | "low";

export interface Step {
  id: string;
  claim: string;
  justification: string;
  refs: string[];
  /** Đối tượng cần tô sáng trên hình khi người dùng chọn bước này. */
  highlight: string[];
}

export interface SubProblem {
  label: string;
  statement: string;
  goal_type: string | null;
  difficulty: number;
  steps: Step[];
  answer: string | null;
  confidence: Confidence;
}

export interface ProblemState {
  latex: string | null;
  topic: string | null;
  difficulty: number;
  subproblems: SubProblem[];
  figure_svg: string | null;
  figure_quality: number | null;
  hints: string[];
  verification: {
    algebra_ok: boolean | null;
    geometry_ok: boolean | null;
    violations: unknown[];
    lemmas_found: string[];
  };
}

export interface StageEvent {
  stage: string;
  label: string;
}
