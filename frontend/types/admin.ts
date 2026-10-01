// Phản chiếu backend/packages/exam/math9_exam/intake.py (lô tài liệu, bài chờ duyệt) và routes/similar.py.

export type ProblemStatus = "pending" | "approved" | "rejected";
export type ProblemFormat = "trac_nghiem" | "dung_sai" | "tra_loi_ngan" | "tu_luan";

export interface DraftProblem {
  id: string;
  number: string;
  group: string | null;
  lead: string | null;
  statement: string;
  format: ProblemFormat;
  options: string[] | null;
  claims: string[] | null;
  answer: string | { letter: string; value: string } | null;
  answer_evidence: string | null;
  topic: string | null;
  goal_type: string;
  difficulty: number;
  needs_figure: boolean;
  status: ProblemStatus;
  warnings: string[];
  duplicate_of?: string;
}

export interface Batch {
  id: string;
  filename: string;
  source: string | null;
  status: "processing" | "ready" | "error";
  error: string | null;
  created_at: string;
  notes: string[];
  problems: DraftProblem[];
}

export interface BatchSummary {
  id: string;
  filename: string;
  source: string | null;
  status: Batch["status"];
  error: string | null;
  created_at: string;
  counts: Record<ProblemStatus, number>;
}

export interface AdminStats {
  bank_builtin: number;
  qdrant: null | {
    mode: "cloud" | "local";
    collection: string;
    total_points: number;
    uploads: number;
    uploads_by_topic: Record<string, number>;
  };
}

export interface SimilarItem {
  id: string;
  statement: string;
  source: string | null;
  format: ProblemFormat;
  options: string[] | null;
  claims: string[] | null;
  topic: string;
  difficulty: number;
  score: number;
}
