"""Kiểm thử tầng RAG — chạy offline với HashingEmbedder, không cần model."""

import pytest
from math9_retrieval.embedder import HashingEmbedder
from math9_retrieval.retriever import Retriever
from math9_retrieval.service import RagService
from math9_retrieval.store import Collection, Doc, load_methods


def _methods() -> list[Doc]:
    return [
        Doc(id="prove_concyclic", collection=Collection.METHODS,
            goal_type="prove_concyclic", modes=["basic", "exam10"], status="reviewed",
            body="Chứng minh đồng viên. Hướng 1: tổng hai góc đối 180 độ. "
                 "Hướng 2: hai đỉnh cùng nhìn một cạnh."),
        Doc(id="find_fixed_point", collection=Collection.METHODS,
            goal_type="find_fixed_point", modes=["exam10"], status="reviewed",
            body="Tìm điểm cố định. Dự đoán bằng vị trí đặc biệt rồi chứng minh."),
        Doc(id="prove_tangent", collection=Collection.METHODS,
            goal_type="prove_tangent", modes=["basic", "exam10"], status="reviewed",
            body="Chứng minh tiếp tuyến. Bán kính vuông góc tại tiếp điểm."),
    ]


def test_goal_type_is_primary_signal():
    """Sổ tay đúng goal_type phải được ưu tiên tuyệt đối, không phụ thuộc từ khóa."""
    r = Retriever(_methods(), HashingEmbedder())
    # Query không chứa từ 'cố định' nhưng goal_type khớp -> vẫn phải trả đúng
    hits = r.search_methods("đường thẳng luôn qua một điểm", "find_fixed_point", "exam10")
    assert hits[0].doc.id == "find_fixed_point"
    assert hits[0].how == "goal_type"


def test_mode_filter_respected():
    """find_fixed_point chỉ có ở exam10; hỏi ở basic phải rơi sang hybrid."""
    r = Retriever(_methods(), HashingEmbedder())
    hits = r.search_methods("điểm cố định", "find_fixed_point", "basic")
    # Không match exact (mode sai) -> hybrid, không được crash
    assert isinstance(hits, list)


def test_hybrid_rescues_wrong_goal_type():
    """Router phân loại sai -> hybrid vẫn tìm được sổ tay liên quan qua từ khóa."""
    r = Retriever(_methods(), HashingEmbedder())
    hits = r.search_methods("chứng minh tứ giác nội tiếp đường tròn", None, "exam10")
    assert any("đồng viên" in h.doc.body or "góc đối" in h.doc.body for h in hits)


def test_unreviewed_methods_blocked(tmp_path):
    """Cổng chặn: sổ tay draft KHÔNG được nạp vào RAG."""
    (tmp_path / "a.md").write_text(
        "---\ngoal_type: prove_concyclic\nstatus: reviewed\n---\nĐã soát.", encoding="utf-8")
    (tmp_path / "b.md").write_text(
        "---\ngoal_type: prove_tangent\nstatus: needs_teacher\n---\nChưa soát.", encoding="utf-8")
    docs = load_methods(tmp_path, require_reviewed=True)
    ids = {d.id for d in docs}
    assert "a" in ids and "b" not in ids


def test_service_returns_prompt_ready_context(tmp_path):
    md = tmp_path / "methods"
    md.mkdir()
    (md / "prove_concyclic.md").write_text(
        "---\ngoal_type: prove_concyclic\nmodes: [exam10]\nstatus: reviewed\n---\n"
        "# Đồng viên\nHướng 1: tổng hai góc đối.", encoding="utf-8")
    svc = RagService(methods_dir=md, problems_dir=tmp_path / "nope")
    ctx = svc.retrieve("chứng minh ABOC nội tiếp", "prove_concyclic", "exam10")
    assert "góc đối" in ctx.method_notes
    assert not ctx.is_empty()


def test_answer_keys_excluded_from_worked(tmp_path):
    """Hướng dẫn chấm (cụt lủn) không được vào kho bài mẫu.

    Mỗi bài mẫu là MỘT file *.json (không phải một dòng jsonl) — dễ cho giáo
    viên mở và soát tay hơn nhiều bài dồn trong một file. Xem data/problems/QUY-CACH.md.
    """
    import json
    pd = tmp_path / "problems"
    pd.mkdir()
    (pd / "hdc.json").write_text(
        json.dumps({"id": "1", "statement": "Giải pt", "solution_type": "answer_key",
                    "steps": [{"claim": "x = 2", "justification": ""}]}, ensure_ascii=False),
        encoding="utf-8")
    (pd / "chi-tiet.json").write_text(
        json.dumps({"id": "2", "statement": "Giải pt", "solution_type": "detailed",
                    "subproblems": [{"label": "a", "goal_type": "solve_equation", "topic": "ALG-6",
                                     "steps": [{"claim": "x = 2", "justification": "vì 2x = 4"}],
                                     "answer": "x = 2"}]}, ensure_ascii=False),
        encoding="utf-8")
    from math9_retrieval.store import load_worked_examples
    docs = load_worked_examples(pd)
    assert len(docs) == 1 and docs[0].id == "2-a"
    assert "vì 2x = 4" in docs[0].body


def test_worked_example_one_doc_per_subproblem(tmp_path):
    """Bài nhiều ý -> nhiều Doc, mỗi ý mang goal_type riêng — đây là đơn vị RAG truy xuất."""
    import json
    pd = tmp_path / "problems"
    pd.mkdir()
    (pd / "bai.json").write_text(json.dumps({
        "id": "b1", "statement": "Cho tam giác ABC...", "solution_type": "detailed", "mode": "exam10",
        "subproblems": [
            {"label": "a", "goal_type": "prove_concyclic", "topic": "GEO-9",
             "steps": [{"claim": "ABOC nội tiếp", "justification": "tổng hai góc đối 180 độ"}]},
            {"label": "b", "goal_type": "prove_perpendicular", "topic": "GEO-5",
             "steps": [{"claim": "OA vuông góc BC", "justification": "OA là trung trực BC"}]},
        ],
    }, ensure_ascii=False), encoding="utf-8")
    from math9_retrieval.store import load_worked_examples
    docs = load_worked_examples(pd)
    assert {d.id for d in docs} == {"b1-a", "b1-b"}
    assert {d.goal_type for d in docs} == {"prove_concyclic", "prove_perpendicular"}


def test_embedder_similarity_sane():
    e = HashingEmbedder()
    v = e.encode(["tứ giác nội tiếp đường tròn",
                  "tứ giác nội tiếp một đường tròn",
                  "giải hệ phương trình bậc nhất"])
    sim_close = sum(a * b for a, b in zip(v[0], v[1]))
    sim_far = sum(a * b for a, b in zip(v[0], v[2]))
    assert sim_close > sim_far
