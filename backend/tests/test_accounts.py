"""Tài khoản + lịch sử: đăng ký/đăng nhập, khóa khi sai nhiều, phiên, cô lập dữ liệu giữa học sinh,
hạn mức giải bài, lưu lượt giải và đề luyện. CSDL SQLite trong bộ nhớ — không đụng Supabase."""

import pytest
from conftest import make_client
from math9_accounts import history, service
from math9_accounts.security import hash_password, verify_password
from math9_accounts.service import AccountError

# ---------- mật khẩu + nghiệp vụ ----------


def test_password_hashing():
    h = hash_password("matkhau-123")
    assert h.startswith("scrypt$") and "matkhau" not in h
    assert verify_password("matkhau-123", h) and not verify_password("sai", h)
    assert hash_password("matkhau-123") != h                  # mỗi lần một salt


def test_create_user_validation(mem_db):
    with pytest.raises(AccountError):
        service.create_user("ab", "matkhau-123", "")               # tên quá ngắn
    with pytest.raises(AccountError):
        service.create_user("Nguyễn Văn A", "matkhau-123", "")     # có dấu/khoảng trắng
    with pytest.raises(AccountError):
        service.create_user("hocsinh1", "1234567", "")             # mật khẩu < 8
    u = service.create_user("HocSinh1", "matkhau-123", "Em A")
    assert u.username == "hocsinh1"                              # chuẩn hóa chữ thường
    with pytest.raises(AccountError, match="đã có"):
        service.create_user("hocsinh1", "matkhau-456", "")


def test_login_lockout_and_generic_errors(mem_db):
    service.create_user("hocsinh1", "matkhau-123", "", must_change_password=False)
    with pytest.raises(AccountError) as unknown:
        service.authenticate("khongco", "x")
    with pytest.raises(AccountError) as wrong:
        service.authenticate("hocsinh1", "sai-mat-khau")
    assert str(unknown.value) == str(wrong.value)               # không lộ tên đăng nhập nào có thật
    for _ in range(service.MAX_FAILED - 1):
        with pytest.raises(AccountError):
            service.authenticate("hocsinh1", "sai-mat-khau")
    with pytest.raises(AccountError, match="tạm khóa"):
        service.authenticate("hocsinh1", "matkhau-123")          # đúng mật khẩu nhưng đang bị khóa


def test_sessions_logout_and_password_change(mem_db):
    u = service.create_user("hocsinh1", "matkhau-123", "", must_change_password=False)
    t1, t2 = service.create_session(u.id), service.create_session(u.id)
    assert service.user_by_token(t1).id == u.id
    assert service.user_by_token("bia-dat") is None
    service.change_password(u.id, "matkhau-123", "matkhau-moi-1", keep_token=t1)
    assert service.user_by_token(t1) and service.user_by_token(t2) is None     # máy khác bị đăng xuất
    service.end_session(t1)
    assert service.user_by_token(t1) is None
    service.reset_password("hocsinh1", "dat-lai-12345")
    assert service.authenticate("hocsinh1", "dat-lai-12345").id == u.id


# ---------- API ----------

def test_api_login_cookie(mem_db):
    from api.routes import history as hist_route

    anon = make_client(hist_route.router, login=False)
    r = anon.post("/api/auth/register", json={"username": "tudangky", "password": "matkhau-123"})
    assert r.status_code in (404, 405)                           # không có tự đăng ký — admin cấp tài khoản

    c = make_client(hist_route.router)
    cookie = c.cookies.get("m9_session")
    assert cookie
    me = c.get("/api/auth/me").json()
    assert me["username"] == "hocsinh1" and me["daily_limit"] > 0
    c.post("/api/auth/logout")
    assert c.get("/api/auth/me").status_code == 401
    r = c.post("/api/auth/login", json={"username": "hocsinh1", "password": "matkhau-123"})
    assert r.status_code == 200 and "httponly" in r.headers["set-cookie"].lower()
    assert c.post("/api/auth/login", json={"username": "hocsinh1", "password": "sai"}).status_code == 400


def test_history_isolated_between_students(mem_db):
    from api.routes import history as hist_route

    a = make_client(hist_route.router, username="hocsinh_a")
    b = make_client(hist_route.router, username="hocsinh_b")
    uid_a = service.authenticate("hocsinh_a", "matkhau-123").id
    rid = history.start_solve(uid_a, "Giải x + 1 = 2", "exam10", None)
    history.finish_solve(rid, {"topic": "ALG-2", "confidence": "high", "subproblems": []})

    assert a.get(f"/api/history/solves/{rid}").json()["state"]["topic"] == "ALG-2"
    assert a.get("/api/history/solves").json()["items"][0]["id"] == rid
    assert b.get(f"/api/history/solves/{rid}").status_code == 404      # người khác không xem được
    assert b.delete(f"/api/history/solves/{rid}").status_code == 404
    assert b.get("/api/history/solves").json()["items"] == []
    assert a.delete(f"/api/history/solves/{rid}").status_code == 200


def test_exam_saved_owned_and_self_marks(mem_db):
    from api.routes import exam as exam_route
    from api.routes import history as hist_route

    a = make_client(exam_route.router, hist_route.router, username="hocsinh_a")
    b = make_client(exam_route.router, hist_route.router, username="hocsinh_b")
    pub = a.post("/api/exam", json={"blueprint": "ha-noi", "seed": 3}).json()
    assert b.get(f"/api/exam/{pub['id']}").status_code == 404           # mã đề của người khác: không mở được
    assert b.post(f"/api/exam/{pub['id']}/submit", json={"responses": {}}).status_code == 404

    res = a.post(f"/api/exam/{pub['id']}/submit", json={"responses": {}}).json()
    again = a.post(f"/api/exam/{pub['id']}/submit", json={"responses": {"q1": "A"}}).json()
    assert again == res                                                  # nộp hai lần: giữ kết quả lần đầu

    proof = next(i for i in res["items"] if i["status"] == "tu_cham")
    r = a.put(f"/api/history/exams/{pub['id']}/self-marks",
              json={"marks": {proof["qid"]: 99, "q-khong-co": 5}}).json()
    assert r["score"] == proof["points"]                                 # chặn ở số điểm của câu, bỏ qid lạ
    lst = a.get("/api/history/exams").json()["items"]
    assert lst[0]["id"] == pub["id"] and lst[0]["submitted_at"] and lst[0]["score"] == proof["points"]
    detail = a.get(f"/api/history/exams/{pub['id']}").json()
    assert "answer" not in str(detail["exam"]["questions"])              # đề công khai; đáp án chỉ trong result


# ---------- giải bài qua API: lưu lịch sử + hạn mức ----------

@pytest.fixture
def solve_client(mem_db, monkeypatch):
    from api.routes import history as hist_route
    from api.routes import solve as solve_route
    from math9_core.agents.critic import CriticAgent
    from math9_core.agents.draftsman import DraftsmanAgent
    from math9_core.agents.parser import ParserAgent
    from math9_core.agents.pedagogue import PedagogueAgent
    from math9_core.agents.router import RouterAgent
    from math9_core.agents.solver import SolverAgent
    from math9_core.graph import Pipeline
    from test_pipeline import FakeLLM

    llm = FakeLLM()
    c = make_client(solve_route.router, hist_route.router)
    c.app.state.pipeline = Pipeline(
        parser=ParserAgent(llm, "fake"), router=RouterAgent(llm, "fake"), solver=SolverAgent(llm, "fake"),
        draftsman=DraftsmanAgent(llm, "fake"), critic=CriticAgent(llm, "fake"), pedagogue=PedagogueAgent(llm, "fake"),
    )
    return c


def test_solve_is_saved_to_history(solve_client):
    from test_pipeline import STATEMENT

    r = solve_client.post("/api/solve", json={"text": STATEMENT, "stream": False})
    assert r.status_code == 200
    body = r.json()
    rec = solve_client.get(f"/api/history/solves/{body['history_id']}").json()
    assert rec["status"] == "done" and rec["question"] == STATEMENT
    assert rec["state"]["confidence"] == body["confidence"] and rec["state"]["figure_svg"]


def test_solve_streaming_saved_and_quota(solve_client, monkeypatch):
    from test_pipeline import STATEMENT

    with solve_client.stream("POST", "/api/solve", json={"text": STATEMENT}) as r:
        body = "".join(r.iter_text())
    assert "event: done" in body and "history_id" in body
    assert solve_client.get("/api/auth/me").json()["solves_today"] == 1
    monkeypatch.setenv("SOLVE_DAILY_LIMIT", "1")
    r = solve_client.post("/api/solve", json={"text": STATEMENT, "stream": False})
    assert r.status_code == 429 and "giới hạn" in r.json()["detail"]


def test_solve_requires_login(mem_db):
    from api.routes import solve as solve_route

    anon = make_client(solve_route.router, login=False)
    assert anon.post("/api/solve", json={"text": "Giải x + 1 = 2"}).status_code == 401
