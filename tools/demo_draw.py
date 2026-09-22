"""Demo: đề bài hình học -> kịch bản dựng hình (LLM) -> engine tính tọa độ -> SVG.

    python tools/demo_draw.py "Cho đường tròn (O) và điểm A nằm ngoài. Kẻ hai tiếp tuyến AB, AC..."
    python tools/demo_draw.py --file de.txt --out demo/out
    python tools/demo_draw.py --construction demo/out/construction.json   # bỏ qua LLM, dựng lại

Kết quả ghi vào thư mục --out: construction.json, figure.svg, index.html (mở bằng trình duyệt).
Sai kịch bản -> gửi lỗi lại cho LLM sửa, tối đa 2 lần (đúng nguyên tắc vòng lặp giới hạn).
"""

from __future__ import annotations

import argparse
import html
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for pkg in ("core", "curriculum", "geometry", "verifier"):
    sys.path.insert(0, str(ROOT / "packages" / pkg))

from jinja2 import Template  # noqa: E402
from math9_core.llm.client import LLMClient, client_from_env, default_model  # noqa: E402
from math9_geometry.construct import build  # noqa: E402
from math9_geometry.dsl import Construction, op_catalog, validate_ops  # noqa: E402
from math9_geometry.layout import best_figure  # noqa: E402
from math9_geometry.primitives import GeometryError  # noqa: E402
from math9_geometry.render_svg import render  # noqa: E402

PROMPT = Template((ROOT / "prompts" / "draftsman.md").read_text(encoding="utf-8"))
MAX_ATTEMPTS = 2


def ask_llm(llm: LLMClient, model: str, statement: str, feedback: str = "") -> tuple[dict, dict]:
    user = PROMPT.render(op_catalog=op_catalog(), latex=statement, retry_feedback=feedback)
    t0 = time.time()
    resp = llm.complete(
        system="Bạn là kỹ sư dựng hình cho phần mềm hình học. Chỉ trả JSON hợp lệ.",
        user=user, model=model, max_tokens=3000, temperature=0.2,
    )
    meta = {"model": resp.model, "tokens_in": resp.tokens_in, "tokens_out": resp.tokens_out,
            "ms": int((time.time() - t0) * 1000)}
    return resp.json(), meta


def try_build(raw: dict) -> tuple[Construction | None, str]:
    """Trả về (construction, thông báo lỗi). Lỗi rỗng nghĩa là dựng được."""
    try:
        c = Construction.model_validate(raw)
    except Exception as e:  # pydantic
        return None, f"JSON không đúng schema: {e}"
    errs = validate_ops(c.ops)
    if errs:
        return None, "Kịch bản không hợp lệ:\n" + "\n".join(f"- {x}" for x in errs)
    try:
        build(c, seed=1)
    except GeometryError as e:
        return None, f"Engine không dựng được: {e}"
    return c, ""


class DrawResult:
    def __init__(self, construction: Construction, svg: str, quality, seed: int, n_points: int, log: list[dict]):
        self.construction, self.svg, self.quality = construction, svg, quality
        self.seed, self.n_points, self.log = seed, n_points, log


def draw(statement: str, llm: LLMClient, model: str, on_event=None) -> DrawResult:
    """Đề bài -> kịch bản (LLM, tối đa MAX_ATTEMPTS lượt) -> hình. Ném RuntimeError nếu thất bại.

    `on_event(kind, payload)` nhận: "calling" {attempt}, "received" {attempt, meta, raw},
    "error" {attempt, error}, "built" {seed, quality}.
    """
    emit = on_event or (lambda k, p: None)
    log: list[dict] = []
    c, feedback, raw = None, "", {}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        emit("calling", {"attempt": attempt})
        raw, meta = ask_llm(llm, model, statement, feedback)
        emit("received", {"attempt": attempt, "meta": meta, "raw": raw})
        c, err = try_build(raw)
        log.append({"attempt": attempt, **meta, "n_ops": len(raw.get("ops", [])), "error": err or None})
        if c:
            break
        emit("error", {"attempt": attempt, "error": err})
        feedback = err + "\n\nKịch bản đã gửi:\n" + json.dumps(raw, ensure_ascii=False)
    if not c:
        raise RuntimeError(f"Không dựng được sau {MAX_ATTEMPTS} lần. Lỗi cuối: {log[-1]['error']}")
    fig, q = best_figure(c)
    emit("built", {"seed": fig.seed, "quality": q.score})
    log.append({"seed": fig.seed, "quality": round(q.score, 2), "n_points": len(fig.points())})
    return DrawResult(c, render(fig), q, fig.seed, len(fig.points()), log)


def write_outputs(out: Path, statement: str, c: Construction, svg: str, quality, log: list[dict]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "construction.json").write_text(c.model_dump_json(indent=2), encoding="utf-8")
    (out / "figure.svg").write_text(svg, encoding="utf-8")
    ops_txt = "\n".join(
        f"{i + 1:2d}. {o.op.value:22s} {o.name or '':6s} {o.args} {o.params or ''}"
        for i, o in enumerate(c.ops)
    )
    page = f"""<!doctype html><meta charset="utf-8"><title>Demo dựng hình</title>
<style>body{{font-family:"Segoe UI",Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px}}
.row{{display:flex;gap:24px;flex-wrap:wrap}} .fig{{flex:1;min-width:420px;border:1px solid #ddd;padding:8px}}
pre{{background:#f6f6f6;padding:12px;overflow:auto;font-size:13px}} .q{{color:#555}}</style>
<h2>Đề bài</h2><p>{html.escape(statement)}</p>
<div class="row"><div class="fig">{svg}<p class="q">Điểm dễ nhìn: {quality.score:.2f} (seed {log[-1].get('seed')})
{' — ' + '; '.join(quality.reasons) if quality.reasons else ''}</p></div>
<div style="flex:1;min-width:380px"><h3>Kịch bản dựng hình ({len(c.ops)} phép)</h3><pre>{html.escape(ops_txt)}</pre>
<h3>Nhật ký</h3><pre>{html.escape(json.dumps(log, ensure_ascii=False, indent=1))}</pre></div></div>"""
    (out / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("statement", nargs="?", help="đề bài (hoặc dùng --file)")
    ap.add_argument("--file", type=Path)
    ap.add_argument("--construction", type=Path, help="dựng từ JSON có sẵn, không gọi LLM")
    ap.add_argument("--model", default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "demo" / "out")
    a = ap.parse_args()

    statement = a.statement or (a.file.read_text(encoding="utf-8").strip() if a.file else "")
    log: list[dict] = []

    if a.construction:
        raw = json.loads(a.construction.read_text(encoding="utf-8"))
        statement = statement or f"(dựng lại từ {a.construction.name})"
        c, err = try_build(raw)
        if not c:
            raise SystemExit(err)
    else:
        if not statement:
            raise SystemExit("Cần đề bài: truyền trực tiếp hoặc --file")
        llm, model = client_from_env(), a.model or default_model()
        print(f"Model: {model}")

        def on_event(kind: str, p: dict) -> None:
            if kind == "calling":
                print(f"[{p['attempt']}/{MAX_ATTEMPTS}] Gọi LLM sinh kịch bản...", end=" ", flush=True)
            elif kind == "received":
                print(f"{p['meta']['ms']} ms, {p['meta']['tokens_out']} token")
            elif kind == "error":
                print(f"    Lỗi: {p['error'].splitlines()[0]}")

        try:
            r = draw(statement, llm, model, on_event)
        except Exception as e:
            raise SystemExit(f"\n{e}")
        c, log = r.construction, r.log

    fig, q = best_figure(c)
    svg = render(fig)
    if not log or "seed" not in log[-1]:
        log.append({"seed": fig.seed, "quality": round(q.score, 2), "n_points": len(fig.points())})
    write_outputs(a.out, statement, c, svg, q, log)

    print(f"\nDựng xong: {len(c.ops)} phép, {len(fig.points())} điểm, độ dễ nhìn {q.score:.2f}")
    print(f"Mở: {a.out / 'index.html'}")


if __name__ == "__main__":
    main()
