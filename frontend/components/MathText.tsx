"use client";

import katex from "katex";
import { mathParts } from "../lib/mathify";

/** Model đôi khi viết LaTeX kiểu \( … \) hoặc \[ … \] — đổi về $…$ để KaTeX vẽ. */
function normalize(text: string): string {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, m) => `$${m}$`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, m) => `$${m}$`);
}

function Tex({ tex }: { tex: string }) {
  return (
    <span
      dangerouslySetInnerHTML={{ __html: katex.renderToString(tex, { throwOnError: false, output: "html" }) }}
    />
  );
}

/**
 * Chữ thường + công thức trong $…$. Công thức viết bằng ký hiệu Unicode ("(−x² + x + 2)/2", "√5")
 * được đổi sang LaTeX (lib/mathify.ts) để hiện phân số, căn, mũ, chỉ số đúng kiểu sách giáo khoa;
 * có sẵn LaTeX (\frac…) thì giữ nguyên.
 */
export function MathText({ text }: { text: string }) {
  const t = text.includes("\\") ? normalize(text) : text;
  if (!t.includes("$")) return <>{t}</>;
  const chunks = t.split(/(\$[^$]+\$)/g);
  return (
    <>
      {chunks.map((p, i) =>
        p.startsWith("$") && p.endsWith("$") && p.length > 2 ? (
          <span key={i}>
            {mathParts(p.slice(1, -1)).map((q, j) =>
              q.kind === "tex" ? <Tex key={j} tex={q.v} /> : <span key={j}>{q.v}</span>,
            )}
          </span>
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}
