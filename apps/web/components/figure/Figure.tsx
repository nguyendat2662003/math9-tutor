"use client";

import { useEffect, useRef } from "react";

/**
 * Hình SVG do engine sinh, mỗi đối tượng bọc trong <g data-name data-kind data-pts>.
 * Khi học sinh chạm vào một bước giải, tô sáng các đối tượng của bước đó và làm mờ phần còn lại.
 */
export function Figure({ svg, highlight }: { svg: string; highlight: string[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    const want = new Set(highlight);
    root.querySelectorAll<SVGGElement>("g[data-name]").forEach((g) => {
      const name = g.dataset.name ?? "";
      const pts = (g.dataset.pts ?? "").split(",").filter(Boolean);
      const pairName = name.length === 2 && want.has(name[0]) && want.has(name[1]);
      const allPts = pts.length >= 2 && pts.every((p) => want.has(p));
      const hit = want.has(name) || pairName || (g.dataset.kind !== "circle" && allPts) ||
        (g.dataset.kind === "point" && want.has(name));
      g.classList.toggle("hl", want.size > 0 && hit);
      g.classList.toggle("dim", want.size > 0 && !hit);
    });
  }, [svg, highlight]);

  return <div className="card figure" ref={ref} dangerouslySetInnerHTML={{ __html: svg }} />;
}
