// Phản chiếu backend/packages/exam/math9_exam/models.py (bản công khai — không có đáp án).

export type ExamFormat = "trac_nghiem" | "tra_loi_ngan" | "dung_sai" | "tu_luan";
export type Level = "de" | "vua" | "kho" | "tron";

export interface ExamQuestion {
  qid: string;
  number: string;
  section: string;
  format: ExamFormat;
  statement: string;
  context: string | null;
  group: string | null;
  options: string[] | null;
  claims: string[] | null;
  points: number;
  topic: string;
  difficulty: number;
  source: string;
  origin: "bank" | "variant";
  auto: boolean;
  hint: string | null;
  /** Hình/biểu đồ của đề — SVG do server vẽ từ data/exam/figures.yaml. */
  figure_svg: string | null;
}

export interface Exam {
  id: string;
  title: string;
  minutes: number;
  blueprint: string;
  seed: number;
  created_at: string;
  total_points: number;
  warnings: string[];
  questions: ExamQuestion[];
}

/** Trắc nghiệm: "A".."D" · trả lời ngắn/tự luận: chuỗi · đúng/sai: mảng theo từng ý. */
export type Answer = string | (boolean | null)[] | null;

export type ItemStatus = "dung" | "sai" | "mot_phan" | "bo_trong" | "tu_cham";

export interface GradedItem {
  qid: string;
  points: number;
  earned: number;
  auto: boolean;
  answer: string;
  solution: string[];
  response: Answer;
  status: ItemStatus;
  n_correct?: number;
}

export interface ExamResult {
  exam_id: string;
  total_points: number;
  auto_score: number;
  self_grade_points: number;
  items: GradedItem[];
}

export interface BlueprintInfo {
  id: string;
  name: string;
  style: string;
  minutes: number;
  based_on: string;
  n_questions: number;
}

export interface BlueprintList {
  blueprints: BlueprintInfo[];
  topics: Record<string, string>;
  bank_size: number;
  templates: number;
}

export interface CustomSpec {
  topics: string[];
  n_trac_nghiem: number;
  n_tra_loi_ngan: number;
  n_tu_luan: number;
  level: Level;
  minutes: number;
}

/** Yêu cầu tạo đề — giữ lại để "làm lại đề này" (cùng seed ra cùng đề). */
export type ExamRequest = { blueprint: string; seed?: number } | { custom: CustomSpec; seed?: number };
