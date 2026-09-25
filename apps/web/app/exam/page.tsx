"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { createExam, fetchBlueprints, getExam, submitExam } from "../../lib/api";
import type { Answer, BlueprintList, Exam, ExamRequest, ExamResult as Result } from "../../types/exam";
import { ExamSetup } from "../../components/exam/ExamSetup";
import { ExamPaper, isAnswered } from "../../components/exam/ExamPaper";
import { ExamResult } from "../../components/exam/ExamResult";

// Bài đang làm lưu trong trình duyệt để lỡ tải lại trang không mất bài.
// Đề và đáp án nằm trên server; ở đây chỉ có id đề + câu trả lời của học sinh.
const KEY = "math9.exam.v1";

interface Saved {
  examId: string;
  request: ExamRequest;
  responses: Record<string, Answer>;
  startedAt: number;
  result?: Result;
  selfMarks?: Record<string, number>;
}

function readSaved(): Saved | null {
  try {
    const raw = localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Saved) : null;
  } catch {
    return null;
  }
}

function writeSaved(s: Saved | null) {
  try {
    if (s) localStorage.setItem(KEY, JSON.stringify(s));
    else localStorage.removeItem(KEY);
  } catch {
    /* chế độ ẩn danh / chặn lưu trữ: vẫn làm bài được, chỉ không khôi phục khi tải lại */
  }
}

export default function ExamPage() {
  const [info, setInfo] = useState<BlueprintList | null>(null);
  const [exam, setExam] = useState<Exam | null>(null);
  const [saved, setSaved] = useState<Saved | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const submitting = useRef(false);

  // Luôn cập nhật từ trạng thái MỚI NHẤT: chọn nhanh nhiều câu liên tiếp mà dựng từ bản
  // cũ trong closure thì lần ghi sau đè mất câu trả lời của lần trước.
  const update = useCallback((fn: (s: Saved | null) => Saved | null) => {
    setSaved((prev) => {
      const next = fn(prev);
      writeSaved(next);
      return next;
    });
  }, []);

  useEffect(() => {
    fetchBlueprints().then(setInfo).catch((e) => setError(`Không tải được danh sách đề: ${e.message}`));
    const s = readSaved();
    if (!s) return;
    getExam(s.examId)
      .then((e) => { setExam(e); setSaved(s); })
      .catch(() => writeSaved(null));              // đề đã hết hạn trên server
  }, []);

  async function start(request: ExamRequest) {
    setBusy(true);
    setError(null);
    try {
      const e = await createExam(request);
      // Lưu seed để "làm lại đề này" ra đúng đề cũ
      setExam(e);
      update(() => ({ examId: e.id, request: { ...request, seed: e.seed }, responses: {}, startedAt: Date.now() }));
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function answer(qid: string, a: Answer) {
    update((s) => (s && !s.result ? { ...s, responses: { ...s.responses, [qid]: a } } : s));
  }

  const submit = useCallback(async (auto: boolean) => {
    if (!exam || !saved || saved.result || submitting.current) return;
    const left = exam.questions.filter((q) => !isAnswered(saved.responses[q.qid])).length;
    if (!auto && left > 0 && !window.confirm(`Còn ${left} câu chưa làm. Em vẫn muốn nộp bài?`)) return;
    submitting.current = true;
    setBusy(true);
    setError(null);
    try {
      const result = await submitExam(exam.id, saved.responses);
      update((s) => (s ? { ...s, result, selfMarks: {} } : s));
      window.scrollTo({ top: 0 });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }, [exam, saved, update]);

  function reset() {
    update(() => null);
    setExam(null);
  }

  return (
    <main className="app">
      <div className="app__head">
        <h1>Luyện đề thi vào 10</h1>
        <span>Đề theo cấu trúc từng tỉnh hoặc tự chọn chuyên đề · chấm ngay khi nộp</span>
      </div>
      {error && <div className="error" style={{ marginBottom: 12 }}>{error}</div>}

      {!exam || !saved ? (
        <ExamSetup info={info} busy={busy} onStart={start} />
      ) : saved.result ? (
        <ExamResult
          exam={exam}
          result={saved.result}
          selfMarks={saved.selfMarks ?? {}}
          onSelfMark={(qid, p) => update((s) => (s ? { ...s, selfMarks: { ...(s.selfMarks ?? {}), [qid]: p } } : s))}
          onRetry={() => start(saved.request)}
          onNew={reset}
        />
      ) : (
        <ExamPaper
          exam={exam}
          responses={saved.responses}
          endsAt={saved.startedAt + exam.minutes * 60_000}
          busy={busy}
          onAnswer={answer}
          onSubmit={submit}
        />
      )}
    </main>
  );
}
