"""Kho đề Qdrant + nhập tài liệu + trang quản trị. Qdrant trong bộ nhớ, LLM giả — không gọi mạng."""

import json
import sys
from pathlib import Path

import pytest
from math9_core.llm.client import LLMResponse
from math9_exam import intake
from math9_exam.bank import load_bank, refresh_bank
from math9_exam.index import ProblemIndex, set_index, text_hash
from math9_retrieval.embedder import HashingEmbedder
from qdrant_client import QdrantClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000a"
    "49444154789c6360000002000100ffff03000006000557bfabd40000000049454e44ae426082"
)

EXTRACTED = {
    "source": "Đề thử Tỉnh X 2027",
    "problems": [
        {"number": "Câu 1", "statement": "Nghiệm của phương trình 3x − 12 = 0 là", "format": "trac_nghiem",
         "options": ["x = 4", "x = −4", "x = 3", "x = 12"], "answer": {"letter": "A", "value": "x = 4"},
         "answer_evidence": "Câu 1: A", "topic": "ALG-2", "goal_type": "solve_equation", "difficulty": 1},
        {"number": "Bài 4a", "group": "Bài 4", "lead": "Cho đường tròn (O) và điểm M nằm ngoài đường tròn.",
         "statement": "Chứng minh tứ giác MAOB nội tiếp.", "format": "tu_luan", "answer": None,
         "topic": "GEO-9", "goal_type": "prove_concyclic", "difficulty": 1},
        {"number": "Bài 4b", "group": "Bài 4", "lead": "Cho đường tròn (O) và điểm M nằm ngoài đường tròn.",
         "statement": "Chứng minh MO vuông góc với AB.", "format": "tu_luan", "answer": None,
         "topic": "GEO-9", "goal_type": "prove_perpendicular", "difficulty": 2},
        {"number": "Câu 2", "statement": "Tính giá trị biểu thức A = √49 + 1.", "format": "tu_luan",
         "answer": "A = 8", "answer_evidence": "A = 7 + 1 = 8", "topic": "KHONG-CO", "difficulty": 1},
    ],
}


class FakeLLM:
    def __init__(self, payload: dict):
        self.payload, self.calls = payload, []

    def complete(self, system, user, *, model, max_tokens=4000, temperature=0.2, thinking=False, images=None):
        self.calls.append({"user": user, "images": images})
        return LLMResponse(text=json.dumps(self.payload, ensure_ascii=False), model=model, finish_reason="stop")


@pytest.fixture
def index(tmp_path, monkeypatch):
    idx = ProblemIndex(QdrantClient(":memory:"), HashingEmbedder())
    set_index(idx)
    monkeypatch.setattr(intake, "INBOX_DIR", tmp_path / "inbox")
    refresh_bank()
    yield idx
    set_index(None)
    refresh_bank()


# ---------- kho Qdrant ----------

def test_index_upsert_search_filter_delete(index):
    index.upsert([
        {"id": "a", "statement": "Giải phương trình x² − 5x + 6 = 0", "topic": "ALG-6", "status": "approved", "origin": "upload"},
        {"id": "b", "statement": "Chứng minh tứ giác ABCD nội tiếp đường tròn", "topic": "GEO-9", "status": "approved", "origin": "upload"},
        {"id": "c", "statement": "Giải phương trình x² − 7x + 10 = 0", "topic": "ALG-6", "status": "pending", "origin": "upload"},
    ])
    assert index.count() == 3
    hits = index.similar("Giải phương trình x² − 3x + 2 = 0", k=3)
    assert hits[0]["id"] == "a"                          # chờ duyệt (c) không bao giờ được gợi ý
    assert all(h["status"] == "approved" for h in hits)
    assert [h["id"] for h in index.similar("tứ giác nội tiếp", topic="GEO-9")] == ["b"]
    assert not index.similar("Giải phương trình x² − 5x + 6 = 0", exclude_hash=text_hash("Giải phương trình x² − 5x + 6 = 0"), topic="ALG-6")
    index.upsert([{"id": "a", "statement": "Giải phương trình x² − 5x + 6 = 0", "topic": "ALG-6", "status": "approved"}])
    assert index.count() == 3                            # cùng id -> ghi đè, không nhân bản
    index.delete(["a"])
    assert index.count() == 2


# ---------- chuẩn hóa + kiểm tra ----------

def test_normalize_validates_and_warns(index):
    probs = intake.normalize(EXTRACTED, "0" * 32, "de.pdf")
    by = {p["number"]: p for p in probs}
    assert by["Câu 1"]["answer"] == {"letter": "A", "value": "x = 4"} and not by["Câu 1"]["warnings"]
    assert by["Bài 4a"]["group"] == by["Bài 4b"]["group"] and by["Bài 4a"]["lead"]
    assert not by["Bài 4a"]["warnings"]                  # chứng minh: không cần đáp số
    assert by["Câu 2"]["topic"] is None and any("chuyên đề" in w for w in by["Câu 2"]["warnings"])


def test_validate_mcq_letter_only_and_missing_options():
    p = intake.validate({"statement": "x = ?", "format": "trac_nghiem", "options": "A. 1; B. 2; C. 3; D. 4",
                         "answer": "C", "answer_evidence": "C", "topic": "ALG-2"})
    assert p["options"] == ["1", "2", "3", "4"] and p["answer"] == {"letter": "C", "value": "3"}
    q = intake.validate({"statement": "x = ?", "format": "trac_nghiem", "options": ["1", "2"], "answer": None, "topic": "ALG-2"})
    assert any("2 phương án" in w for w in q["warnings"]) and any("chưa có đáp án" in w for w in q["warnings"])
    f = intake.validate({"statement": "Cho tam giác ABC như hình vẽ. Tính góc A.", "format": "tu_luan",
                         "answer": "60°", "answer_evidence": "60°", "topic": "GEO-9"})
    assert f["needs_figure"]


def test_duplicates_against_builtin_bank_and_within_batch(index):
    builtin = load_bank(include_uploads=False).items[0]
    raw = {"problems": [
        {"number": "1", "statement": builtin.statement, "format": builtin.format, "topic": builtin.topic,
         "options": builtin.options, "answer": builtin.answer, "answer_evidence": "x"},
        {"number": "2", "statement": "Bài mới hoàn toàn: tính 2 + 2.", "format": "tu_luan", "answer": "4",
         "answer_evidence": "4", "topic": "ALG-2"},
        {"number": "3", "statement": "Bài mới hoàn toàn:  tính 2 + 2 .", "format": "tu_luan", "answer": "4",
         "answer_evidence": "4", "topic": "ALG-2"},
    ]}
    probs = intake.normalize(raw, "1" * 32, "x.pdf")
    intake.mark_duplicates(probs, index)
    assert probs[0]["duplicate_of"] == builtin.id
    assert "duplicate_of" not in probs[1]
    assert probs[2]["duplicate_of"] == probs[1]["id"]    # trùng trong cùng lô (khác khoảng trắng)


# ---------- duyệt -> vào kho luyện đề ----------

def test_process_approve_and_bank_merge(index, tmp_path):
    llm = FakeLLM(EXTRACTED)
    img = tmp_path / "de.png"
    img.write_bytes(PNG)
    batch = intake.new_batch("de.png")
    intake.process_upload(batch, img, llm, "m", index)
    assert batch["status"] == "ready" and len(batch["problems"]) == 4
    assert llm.calls[0]["images"] == [str(img)]          # ảnh -> VLM đọc
    assert "KHÔNG TỰ GIẢI" in llm.calls[0]["user"]

    ids = [p["id"] for p in batch["problems"]]
    n, skipped = intake.approve(batch, ids, index)
    assert n == 3 and len(skipped) == 1 and "chuyên đề" in skipped[0]     # Câu 2 chưa có chuyên đề
    assert intake.load_batch(batch["id"])["problems"][0]["status"] == "approved"

    refresh_bank()
    bank = load_bank()
    up = [x for x in bank.items if x.id.startswith("up-")]
    assert len(up) == 3
    group = [x for x in up if x.group]
    assert len(group) == 2 and group[0].lead and group[0].part.startswith("Chứng minh")
    assert group[0].group in bank.groups                                     # bài nhiều ý dùng được làm "group"


# ---------- API quản trị + gợi ý tương tự ----------

@pytest.fixture
def client(index, monkeypatch, mem_db):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from api.routes import admin, similar

    monkeypatch.setattr(admin, "_llm", lambda: (FakeLLM(EXTRACTED), "m"))
    from conftest import make_client

    return make_client(admin.router, similar.router, username="admin", role="admin")


def test_admin_requires_admin_account(index, mem_db):
    from conftest import make_client

    from api.routes import admin

    assert make_client(admin.router, login=False).get("/api/admin/batches").status_code == 401
    assert make_client(admin.router, username="hocsinh").get("/api/admin/batches").status_code == 403


def test_admin_rejects_non_documents(client):
    r = client.post("/api/admin/documents", files={"file": ("x.pdf", b"khong phai pdf" * 10, "application/pdf")})
    assert r.status_code == 415
    assert client.get("/api/admin/batches/../../etc").status_code in (400, 404)


def test_admin_full_flow_and_similar(client):
    r = client.post("/api/admin/documents", files={"file": ("de.png", PNG, "image/png")})
    assert r.status_code == 200
    bid = r.json()["id"]
    b = client.get(f"/api/admin/batches/{bid}").json()      # TestClient chạy xong tác vụ nền
    assert b["status"] == "ready"
    c2 = next(p for p in b["problems"] if p["number"] == "Câu 2")
    fixed = client.patch(f"/api/admin/batches/{bid}/problems/{c2['id']}", json={"topic": "ALG-3"}).json()
    assert fixed["topic"] == "ALG-3" and not any("chuyên đề" in w for w in fixed["warnings"])
    assert client.patch(f"/api/admin/batches/{bid}/problems/{c2['id']}",
                        json={"status": "approved"}).status_code == 400          # không cho tự đổi trạng thái

    res = client.post(f"/api/admin/batches/{bid}/approve", json={"ids": [p["id"] for p in b["problems"]]}).json()
    assert res["approved"] == 4 and not res["skipped"]
    stats = client.get("/api/admin/stats").json()
    assert stats["qdrant"]["uploads"] == 4

    sim = client.get("/api/similar", params={"text": "Tìm nghiệm của phương trình 3x − 12 = 0"}).json()
    assert sim["enabled"] and sim["items"]
    assert all("answer" not in it for it in sim["items"])                   # không lộ đáp án

    un = client.post(f"/api/admin/batches/{bid}/unpublish", json={"ids": [c2["id"]]}).json()
    assert un["unpublished"] == 1 and client.get("/api/admin/stats").json()["qdrant"]["uploads"] == 3
