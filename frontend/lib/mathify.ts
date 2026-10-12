// Đổi công thức viết bằng ký hiệu Unicode ("(−x² + x + 2)/2", "1 ± √5", "x₁") sang LaTeX cho KaTeX.
// Model chỉ cần bọc công thức trong $…$ — không phải viết LaTeX (dấu gạch chéo ngược dễ hỏng trong JSON).
// Có sẵn "\" trong đoạn thì coi là LaTeX thật và giữ nguyên.

export interface Part {
  kind: "text" | "tex";
  v: string;
}

const SUP: Record<string, string> = {
  "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
  "ⁿ": "n", "⁺": "+", "⁻": "-",
};
const SUB: Record<string, string> = {
  "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
  "ₙ": "n", "ₓ": "x",
};
const SYMBOLS: Record<string, string> = {
  "−": "-", "–": "-", "·": "\\cdot ", "×": "\\times ", "÷": "\\div ", "≤": "\\le ", "≥": "\\ge ", "≠": "\\ne ",
  "≈": "\\approx ", "±": "\\pm ", "∓": "\\mp ", "∞": "\\infty ", "π": "\\pi ", "∆": "\\Delta ", "Δ": "\\Delta ",
  "°": "^{\\circ}", "∠": "\\angle ", "⊥": "\\perp ", "∥": "\\parallel ", "△": "\\triangle ", "⇒": "\\Rightarrow ",
  "⇔": "\\Leftrightarrow ", "→": "\\to ", "∈": "\\in ", "∉": "\\notin ", "∪": "\\cup ", "∩": "\\cap ",
  "⊂": "\\subset ", "∅": "\\varnothing ", "…": "\\ldots ", "α": "\\alpha ", "β": "\\beta ", "γ": "\\gamma ",
  "δ": "\\delta ", "θ": "\\theta ", "λ": "\\lambda ", "μ": "\\mu ", "φ": "\\varphi ", "ω": "\\omega ",
  "⌢": "\\frown ", "≡": "\\equiv ", "∼": "\\sim ", "≅": "\\cong ", "∀": "\\forall ", "∃": "\\exists ",
};
const LBRACE = "";
const RBRACE = "";
const LATIN_VI = /[À-ɏḀ-ỿ]/;      // có dấu tiếng Việt -> là chữ, không phải ký hiệu
const ATOM = /[A-Za-z0-9²³⁴⁵⁶⁷⁸⁹ⁿ₀-₉π.]/;

/** Vị trí dấu ngoặc ghép với ngoặc tại i (dir=1: ngoặc mở, -1: ngoặc đóng); -1 nếu không ghép được. */
function match(s: string, i: number, open: string, close: string, dir: 1 | -1): number {
  let depth = 0;
  for (let j = i; j >= 0 && j < s.length; j += dir) {
    if (s[j] === (dir === 1 ? open : close)) depth++;
    else if (s[j] === (dir === 1 ? close : open) && --depth === 0) return j;
  }
  return -1;
}

/** √5, √x, √(x² + 1) -> \sqrt{…} */
function sqrtPass(s: string): string {
  let out = "";
  for (let i = 0; i < s.length; i++) {
    if (s[i] !== "√") { out += s[i]; continue; }
    let inner = "";
    let j = i + 1;
    if (s[j] === "(") {
      const k = match(s, j, "(", ")", 1);
      if (k > 0) { inner = s.slice(j + 1, k); j = k + 1; }
    } else {
      const m = /^(?:\d+(?:[.,]\d+)?|[A-Za-z])/.exec(s.slice(j));
      if (m) { inner = m[0]; j += m[0].length; }
    }
    out += inner ? `\\sqrt{${core(inner)}}` : "\\surd ";
    i = j - 1;
  }
  return out;
}

/** Lấy "nguyên tử" liền kề dấu / : chữ-số-mũ, nhóm (…), hoặc \sqrt{…}. dir=-1 lấy bên trái, 1 bên phải. */
function atomAt(s: string, from: number, dir: 1 | -1): [number, number] | null {
  let j = from;
  const step = (): boolean => {
    const c = s[j];
    if (c === undefined) return false;
    if (ATOM.test(c)) { j += dir; return true; }
    if ((dir === -1 && c === ")") || (dir === 1 && c === "(")) {
      const k = dir === -1 ? match(s, j, "(", ")", -1) : match(s, j, "(", ")", 1);
      if (k < 0) return false;
      j = k + dir;
      return true;
    }
    if (dir === -1 && c === "}") {
      const k = match(s, j, "{", "}", -1);
      if (k < 0) return false;
      j = k - 1;
      if (s.slice(0, k).endsWith("\\sqrt")) j -= 5;
      return true;
    }
    if (dir === 1 && s.startsWith("\\sqrt{", j)) {
      const k = match(s, j + 5, "{", "}", 1);
      if (k < 0) return false;
      j = k + 1;
      return true;
    }
    return false;
  };
  while (step());
  const [a, b] = dir === -1 ? [j + 1, from] : [from, j - 1];
  return b >= a ? [a, b] : null;
}

const unwrap = (x: string) => (x.startsWith("(") && match(x, 0, "(", ")", 1) === x.length - 1 ? x.slice(1, -1) : x);

/** a/b -> \dfrac{a}{b}; (…)/2 bỏ ngoặc ngoài. */
function fracPass(s: string): string {
  for (let i = 0; i < s.length; i++) {
    if (s[i] !== "/") continue;
    let l = i - 1;
    while (s[l] === " ") l--;
    let r = i + 1;
    while (s[r] === " ") r++;
    const L = atomAt(s, l, -1);
    const R = atomAt(s, r, 1);
    if (!L || !R) continue;
    const num = unwrap(s.slice(L[0], L[1] + 1));
    const den = unwrap(s.slice(R[0], R[1] + 1));
    const frac = `\\dfrac{${num}}{${den}}`;
    s = s.slice(0, L[0]) + frac + s.slice(R[1] + 1);
    i = L[0] + frac.length - 1;
  }
  return s;
}

function scriptsPass(s: string): string {
  return s
    .replace(/[⁰¹²³⁴⁵⁶⁷⁸⁹ⁿ⁺⁻]+/g, (m) => `^{${[...m].map((c) => SUP[c]).join("")}}`)
    .replace(/[₀-₉ₙₓ]+/g, (m) => `_{${[...m].map((c) => SUB[c]).join("")}}`);
}

function core(s: string): string {
  s = fracPass(sqrtPass(s));
  s = scriptsPass(s);
  s = s.replace(/[^\x00-\x7F]/g, (c) => SYMBOLS[c] ?? c);
  s = s.replace(/(\d),(?=\d)/g, "$1{,}");                                        // số thập phân kiểu Việt: 1,5
  s = s.replace(/(?<![\\A-Za-z])(sin|cos|tan|cot|log|ln|lim|max|min)(?![A-Za-z])/g, "\\$1 ");
  return s;
}

/** Một đoạn công thức Unicode -> LaTeX. */
export function toLatex(src: string): string {
  if (src.includes("\\")) return src;
  let s = src.normalize("NFC").replace(/\{/g, LBRACE).replace(/\}/g, RBRACE);
  s = core(s);
  return s
    .replace(/[%&#]/g, (c) => `\\${c}`)
    .replace(new RegExp(LBRACE, "g"), "\\{")
    .replace(new RegExp(RBRACE, "g"), "\\}");
}

/**
 * Nội dung giữa hai dấu $ -> các mảnh. Chữ tiếng Việt lỡ nằm trong $…$ ("x hoặc y") được tách ra
 * thành chữ thường: KaTeX không có phông cho dấu tiếng Việt, ký hiệu mới đưa cho KaTeX.
 */
export function mathParts(src: string): Part[] {
  if (src.includes("\\")) return [{ kind: "tex", v: src }];
  const s = src.normalize("NFC");
  const words = [...s.matchAll(/\p{L}+/gu)].map((m) => ({ w: m[0], at: m.index ?? 0, vi: LATIN_VI.test(m[0]) }));
  // chữ Việt có dấu là chữ; từ không dấu dài ≥2 kẹp giữa hai chữ Việt cũng là chữ ("Từ ta có")
  const isText = words.map((x, i) => x.vi || (x.w.length >= 2 && words[i - 1]?.vi && words[i + 1]?.vi
    && /^\s+$/.test(s.slice(words[i - 1].at + words[i - 1].w.length, x.at))
    && /^\s+$/.test(s.slice(x.at + x.w.length, words[i + 1].at))));
  const parts: Part[] = [];
  let pos = 0;
  const pushTex = (t: string) => {
    if (!t) return;
    if (!t.trim()) { parts.push({ kind: "text", v: t }); return; }
    const lead = /^\s*/.exec(t)![0];
    const tail = /\s*$/.exec(t)![0];
    if (lead) parts.push({ kind: "text", v: lead });            // KaTeX bỏ khoảng trắng đầu/cuối — giữ lại ở ngoài
    parts.push({ kind: "tex", v: toLatex(t.trim()) });
    if (tail) parts.push({ kind: "text", v: tail });
  };
  for (let i = 0; i < words.length; i++) {
    if (!isText[i]) continue;
    let end = i;
    while (isText[end + 1] && /^\s+$/.test(s.slice(words[end].at + words[end].w.length, words[end + 1].at))) end++;
    pushTex(s.slice(pos, words[i].at));
    parts.push({ kind: "text", v: s.slice(words[i].at, words[end].at + words[end].w.length) });
    pos = words[end].at + words[end].w.length;
    i = end;
  }
  pushTex(s.slice(pos));
  return parts;
}
