"use client";

import { useEffect, useState } from "react";
import { fetchSimilar } from "../../lib/api";
import type { SimilarItem } from "../../types/admin";
import { MathText } from "../MathText";

const LEVEL = ["", "Nhận biết", "Vận dụng", "Vận dụng cao"];

/** Giải xong một bài -> gợi ý vài bài gần nghĩa trong kho đề (Qdrant) để luyện thêm. */
export function SimilarProblems({ text, topic, onPick }: { text: string; topic: string | null; onPick: (t: string) => void }) {
  const [items, setItems] = useState<SimilarItem[] | null>(null);

  useEffect(() => {
    let alive = true;
    setItems(null);
    if (text.trim().length < 10) return;
    fetchSimilar(text, topic)
      .then((r) => alive && setItems(r.enabled ? r.items : []))
      .catch(() => alive && setItems([]));
    return () => {
      alive = false;
    };
  }, [text, topic]);

  if (!items || items.length === 0) return null;
  return (
    <div className="card similar">
      <h3>Bài tương tự để luyện thêm</h3>
      <ol>
        {items.map((it) => {
          const full =
            it.statement +
            (it.options ? "\n" + it.options.map((o, i) => `${"ABCD"[i]}. ${o}`).join("; ") : "") +
            (it.claims ? "\n" + it.claims.map((c, i) => `${"abcd"[i]}) ${c}`).join(" ") : "");
          return (
            <li key={it.id}>
              <div className="similar__text"><MathText text={full} /></div>
              <div className="row similar__meta">
                <span className="chip chip--muted">{it.topic}</span>
                <span className="muted">{LEVEL[it.difficulty] ?? ""}{it.source ? ` · ${it.source}` : ""}</span>
                <button type="button" className="linkbtn" onClick={() => onPick(full)}>Làm bài này</button>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
