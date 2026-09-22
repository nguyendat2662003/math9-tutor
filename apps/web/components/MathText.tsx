"use client";

import katex from "katex";

/** Render chuỗi có thể chứa $...$ (KaTeX). Solver xuất chủ yếu Unicode, KaTeX chỉ là dự phòng. */
export function MathText({ text }: { text: string }) {
  if (!text.includes("$")) return <>{text}</>;
  const parts = text.split(/(\$[^$]+\$)/g);
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
