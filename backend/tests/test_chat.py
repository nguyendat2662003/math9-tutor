"""Hỏi đáp sau khi giải: ngữ cảnh gửi model, stream qua API, lưu lịch sử, giới hạn, cô lập người dùng."""

from conftest import make_client
from math9_core.llm.client import LLMClient, LLMResponse
from math9_core.tutor import chapter_of, system_prompt
from test_accounts import solve_client  # noqa: F401  (fixture dùng chung)
from test_pipeline import STATEMENT

STATE = {
    "raw_input": "Cho tam giác ABC nội tiếp (O)...", "latex": None, "mode": "exam10", "topic": "GEO-9",
    "confidence": "high", "verification": {"geometry_ok": True, "algebra_ok": None},
    "subproblems": [{"label": "a", "statement": "Chứng minh ABOC nội tiếp", "answer": None, "steps": [
        {"id": "a1", "claim": "∠ABO = 90°", "justification": "tiếp tuyến vuông góc bán kính"},
        {"id": "a2", "claim": "ABOC nội tiếp", "justification": "tổng hai góc đối bằng 180°"}]}],
}


class TutorLLM(LLMClient):
    """LLM giả cho hỏi đáp: ghi lại prompt, trả một câu có nhắc bước."""

    def __init__(self):
        self.systems, self.users = [], []

    def complete(self, system, user, *, model, max_tokens=4000, temperature=0.2, thinking=False, images=None):
        self.systems.append(system)
        self.users.append(user)
        return LLMResponse(text="Ở [bước a1], tiếp tuyến vuông góc với bán kính nên ∠ABO = 90°.", model=model,
                           tokens_in=100, tokens_out=20)


def test_chapter_of():
    assert chapter_of("GEO-9") == "Chương IX" and chapter_of("ALG-1") == "Chương I" and chapter_of(None) is None


def test_system_prompt_has_steps_chapter_and_rules():
    p = system_prompt(STATE)
    assert "[bước a1] ∠ABO = 90°" in p and "[bước a2]" in p
    assert "Chương IX" in p and "Góc nội tiếp" in p               # tên chuyên đề từ bản đồ chương trình
    assert "Không bao giờ ghi số bài" in p                                  # không bịa số bài SGK
    assert "[Chương IX] Góc nội tiếp chắn nửa đường tròn là góc vuông" in p   # định lí kèm đúng chương của nó
    # Bài thuộc Chương V vẫn thấy định lí tứ giác nội tiếp gắn nhãn Chương IX (không gán nhầm chương của bài)
    p5 = system_prompt(STATE | {"topic": "GEO-5"})
    assert "Chương V —" in p5 and "[Chương IX] Trong tứ giác nội tiếp, tổng hai góc đối bằng 180 độ" in p5
    assert "CHƯA được máy kiểm chứng" not in p
    assert "CHƯA được máy kiểm chứng" in system_prompt(STATE | {"confidence": "low"})


def _solve(c) -> str:
    r = c.post("/api/solve", json={"text": STATEMENT, "stream": False})
    assert r.status_code == 200
    return r.json()["history_id"]


def _chat_client(solve_client):  # noqa: F811
    from api.routes import chat

    solve_client.app.include_router(chat.router)
    return solve_client


def test_chat_stream_saved_and_context(solve_client, monkeypatch):  # noqa: F811
    c = _chat_client(solve_client)
    sid = _solve(c)
    tutor = TutorLLM()
    c.app.state.pipeline.solver.llm = tutor                         # sau khi giải xong, hỏi đáp dùng LLM giả khác

    with c.stream("POST", f"/api/chat/{sid}", json={"message": "Vì sao góc ABO bằng 90 độ?"}) as r:
        assert r.status_code == 200
        body = "".join(r.iter_text())
    assert "event: token" in body and "event: done" in body and "[bước a1]" in body
    assert "ABOC nội tiếp" in tutor.systems[0]                      # ngữ cảnh là đúng bài vừa giải

    msgs = c.get(f"/api/chat/{sid}").json()
    assert [m["role"] for m in msgs["messages"]] == ["user", "assistant"]
    assert msgs["remaining"] == 14

    with c.stream("POST", f"/api/chat/{sid}", json={"message": "Còn cách khác không?"}) as r:
        "".join(r.iter_text())
    assert "Vì sao góc ABO bằng 90 độ?" in tutor.users[1]            # lượt hỏi trước được gửi kèm


def test_chat_limits_and_isolation(solve_client, monkeypatch):  # noqa: F811
    from api.routes import chat

    c = _chat_client(solve_client)
    sid = _solve(c)
    c.app.state.pipeline.solver.llm = TutorLLM()
    monkeypatch.setenv("CHAT_PER_SOLVE_LIMIT", "1")
    with c.stream("POST", f"/api/chat/{sid}", json={"message": "Câu 1"}) as r:
        "".join(r.iter_text())
    r = c.post(f"/api/chat/{sid}", json={"message": "Câu 2"})
    assert r.status_code == 429 and "tối đa 1" in r.json()["detail"]

    other = make_client(chat.router, username="hocsinh_khac")
    assert other.post(f"/api/chat/{sid}", json={"message": "xin xem"}).status_code == 404
    assert other.get(f"/api/chat/{sid}").status_code == 404
    assert c.post("/api/chat/khong-co-bai-nay", json={"message": "?"}).status_code == 404
    assert c.post(f"/api/chat/{sid}", json={"message": ""}).status_code == 422


def test_deleting_solve_deletes_chat(solve_client):  # noqa: F811
    c = _chat_client(solve_client)
    sid = _solve(c)
    c.app.state.pipeline.solver.llm = TutorLLM()
    with c.stream("POST", f"/api/chat/{sid}", json={"message": "Hỏi"}) as r:
        "".join(r.iter_text())
    assert c.delete(f"/api/history/solves/{sid}").status_code == 200
    assert c.get(f"/api/chat/{sid}").status_code == 404
    from math9_accounts import db
    from math9_accounts.models import ChatMessage
    from sqlalchemy import func, select

    with db.session() as s:
        assert s.scalar(select(func.count()).select_from(ChatMessage)) == 0
