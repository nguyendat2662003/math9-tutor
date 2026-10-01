"use client";

import katex from "katex";

/** Model đôi khi viết LaTeX kiểu \( … \) hoặc \[ … \] dù đã dặn dùng Unicode — đổi về $…$ để KaTeX vẽ. */
function normalize(text: string): string {
  return text
    .replace(/\\\[([\s\S]+?)\\\]/g, (_, m) => `$${m}$`)
    .replace(/\\\(([\s\S]+?)\\\)/g, (_, m) => `$${m}$`);
}

/** Render chuỗi có thể chứa $...$ (KaTeX). Solver xuất chủ yếu Unicode, KaTeX chỉ là dự phòng. */
export function MathText({ text }: { text: string }) {
  const t = text.includes("\\") ? normalize(text) : text;
  if (!t.includes("$")) return <>{t}</>;
  const parts = t.split(/(\$[^$]+\$)/g);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("$") && p.endsWith("$") && p.length > 2 ? (
          <span
            key={i}
            dangerouslySetInnerHTML={{
              __html: katex.renderToString(p.slice(1, -1), { throwOnError: false, output: "html" }),
            }}
          />
        ) : (
          <span key={i}>{p}</span>
        ),
      )}
    </>
  );
}
