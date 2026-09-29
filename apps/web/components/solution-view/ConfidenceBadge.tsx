import type { ProblemState } from "../../types/state";

const TEXT = {
  high: "Lời giải đã được kiểm chứng bằng máy (SymPy / dựng hình 5 cấu hình).",
  partial: "Một phần lời giải chưa kiểm chứng được — hãy đọc kỹ và đối chiếu.",
  low: "Chưa kiểm chứng được. Chỉ dùng để tham khảo hướng đi, không chép.",
};

export function reasons(s: ProblemState): string[] {
  const v = s.verification;
  const g = v.detail.geometry;
  const out: string[] = [];
  if (v.algebra_ok === true) out.push("SymPy khớp đáp án");
  if (v.algebra_ok === false) {
    const bad = v.detail.algebra?.results?.filter((r) => !r.ok).length ?? 0;
    out.push(`SymPy giải lại KHÔNG khớp (${bad} phép kiểm)`);
  }
  if (v.geometry_ok === true && g) out.push(`hình đúng trên ${g.n_configs}/5 cấu hình`);
  if (g?.failures?.length) out.push(`kết luận SAI khi kiểm bằng số: ${g.failures.join(", ")}`);
  if (g?.unresolved?.length) out.push(`không kiểm được: ${g.unresolved.map((u) => u.split(":")[0]).join(", ")}`);
  if (g?.build_errors?.length) out.push(`không dựng được hình ở ${g.build_errors.length} cấu hình`);
  if (v.cross_check.length) out.push(v.cross_check.join("; "));
  if (v.violations.length) out.push(`vượt chương trình: ${v.violations.map((x) => x.detail).join("; ")}`);
  if (s.attempts) out.push(`đã giải lại ${s.attempts} lần`);
  return out;
}

const ICON = { high: "✅", partial: "⚠️", low: "🤔" };

export function ConfidenceBadge({ s }: { s: ProblemState }) {
  const rs = reasons(s);
  return (
    <div className={`conf conf--${s.confidence}`}>
      <span className="conf__icon" aria-hidden>{ICON[s.confidence]}</span>
      <div>
        <strong>{s.confidence === "high" ? "Đã kiểm chứng" : s.confidence === "partial" ? "Kiểm chứng một phần" : "Chưa kiểm chứng"}</strong>
        <span style={{ fontSize: 14 }}>
          {TEXT[s.confidence]}
          {rs.length > 0 && <> ({rs.join(" · ")})</>}
        </span>
      </div>
    </div>
  );
}
