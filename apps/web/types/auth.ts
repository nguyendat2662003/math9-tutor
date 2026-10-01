// Phản chiếu apps/api/routes/auth.py và routes/history.py.

import type { Answer, Exam, ExamRequest, ExamResult } from "./exam";
import type { ProblemState } from "./state";

export interface Me {
  username: string;
  display_name: string;
  role: "admin" | "student";
  /** Mật khẩu do admin cấp: phải đổi trước khi dùng */
  must_change_password: boolean;
  solves_today?: number;
  daily_limit?: number;
}

export interface HistoryPage<T> {
  items: T[];
  more: boolean;
}

export interface SolveHistoryItem {
  id: string;
  created_at: string;
  status: "running" | "done" | "error";
  question: string;
  has_image: boolean;
  topic: string | null;
  confidence: "high" | "partial" | "low" | null;
}

export interface SolveHistoryDetail {
  id: string;
  created_at: string;
  status: SolveHistoryItem["status"];
  question: string;
  has_image: boolean;
  error: string | null;
  state: ProblemState | null;
}

export interface ExamHistoryItem {
  id: string;
  title: string;
  blueprint: string;
  created_at: string;
  submitted_at: string | null;
  score: number | null;
  total: number;
  n_questions: number;
}

export interface ExamHistoryDetail {
  id: string;
  exam: Exam;
  request: ExamRequest;
  responses: Record<string, Answer> | null;
  result: ExamResult | null;
  self_marks: Record<string, number>;
  created_at: string;
  submitted_at: string | null;
  score: number | null;
  total: number;
}

export interface AdminUser {
  username: string;
  display_name: string;
  role: "admin" | "student";
  active: boolean;
  must_change_password: boolean;
  solves: number;
  created_at: string | null;
  last_login_at: string | null;
}

/** Kết quả tạo tài khoản: mật khẩu tự sinh chỉ hiện MỘT lần này. */
export interface CreatedAccount {
  line: string;
  username: string;
  display_name: string;
  ok: boolean;
  password?: string;
  error?: string;
}
