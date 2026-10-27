# 02 — Công việc theo package

Với mỗi package: đã xong gì, thiếu gì, và việc cụ thể tiếp theo. Ký hiệu:
✅ xong · ⚙️ khung có sẵn · 🔲 chưa làm.

---

## geometry ✅

Engine dựng hình. Chạy được, có test.

**Đã xong:** phép toán hình học cơ bản, DSL kịch bản dựng hình, engine thực thi
tuần tự, giải ràng buộc số (scipy), chấm điểm hình đẹp, render SVG chuẩn Việt Nam.

**Còn thiếu:**
- 🔲 Xuất lệnh JSXGraph (`export_jsx.py`) — để hình tương tác được trên web.
  Hiện chỉ có SVG tĩnh.
- 🔲 Thêm phép dựng khi gặp bài thực tế cần: hiện DSL phủ ~30 phép, đủ cho phần
  lớn nhưng sẽ thiếu vài trường hợp hiếm.
- 🔲 Vẽ theo từng bước: renderer đã nhận `up_to_step` nhưng chưa test kỹ với
  bài nhiều bước.

**Việc tiếp theo:** viết `export_jsx.py`, cần khi làm frontend hình học (Sprint 6).

---

## verifier ✅

Kiểm chứng bằng code. Chạy được, có test.

**Đã xong:** 13 vị từ hình học, kiểm chứng trên 5 cấu hình ngẫu nhiên, SymPy
cho đại số, dò bổ đề tự động, đối chiếu chéo lời giải với hình.

**Còn thiếu:**
- 🔲 Mở rộng vị từ khi gặp dạng kết luận mới (ví dụ "tiếp xúc trong/ngoài").
- 🔲 Verifier đại số hiện cần Solver xuất `algebra_checks` đúng định dạng —
  phải test khi Solver thật chạy.

**Việc tiếp theo:** không có việc gấp; mở rộng theo nhu cầu thực tế từ eval.

---

## curriculum ✅ (code) / ⚙️ (nội dung — chờ giáo viên soát)

Guardrail chương trình. Code chạy được; nội dung đã soạn đủ, cần giáo viên soát.

**Đã xong (code):** schema bản đồ chương trình, loader YAML, guardrail 2 lớp
(chặn từ khóa + đối chiếu căn cứ), phân biệt được 3 chế độ.

**Đã xong (nội dung):** 10/10 file chuyên đề theo đúng số chương sách KNTT
(`ALG-1`, `ALG-2`, `ALG-3`, `GEO-4`, `GEO-5`, `ALG-6`, `STA-7`, `PRO-8`, `GEO-9`,
`GEO-10`), phủ toàn bộ mã công cụ mà sổ tay tham chiếu (có test kiểm tra).

**Còn thiếu (giáo viên xác nhận):**
- 🔲 Bốn điểm cần chốt trong `data/methods/so-tay-toan-9/_BAN-DO-CHUONG-TRINH.md`.
  Hiện `T-TANGENT-CHORD-ANGLE` (góc tạo bởi tia tiếp tuyến và dây) và `T-LOCUS`
  (quỹ tích) tạm để `modes: [advanced]` — nếu giáo viên xác nhận vẫn dạy, mở
  lại `exam10`.
- 🔲 Soát `aliases` từng công cụ: đây là chuỗi mà guardrail lớp 2 khớp với
  `justification` của Solver, nên phải khớp cách giáo viên thực sự viết căn cứ.

**Việc tiếp theo:** giáo viên soát 10 file YAML song song với soát sổ tay. Xem `04`.

---

## retrieval ✅ (code) / 🔲 (nội dung)

Tầng RAG. Code chạy được; kho cần dữ liệu.

**Đã xong (code):** hybrid search (BM25 + vector + RRF), 3 collection tách biệt,
embedder đổi được, cổng chặn sổ tay chưa soát, loại hướng dẫn chấm khỏi kho mẫu.

**Còn thiếu:**
- 🔲 Nối `LocalEmbedder` (bge-m3) thật — hiện mặc định HashingEmbedder cho test.
- 🔲 Chuyển sang pgvector khi kho vượt ~2000 tài liệu.
- 🔲 Kho `methods` và `worked_examples` đang rỗng — chờ nội dung.

**Việc tiếp theo:** cài sentence-transformers, đổi embedder mặc định khi có
sổ tay thật để nạp.

---

## ingest ✅

Nhập dữ liệu. Chạy được, có test.

**Đã xong:** fetch tôn trọng robots.txt + rate limit + cache, trích PDF/DOCX/HTML,
chuẩn hóa tiếng Việt, tách bài/ý, chấm chất lượng, khử trùng lặp MinHash,
hàng đợi soát cho giáo viên.

**Còn thiếu:**
- 🔲 Adapter cho nguồn cụ thể — mỗi site một file, viết khi có link. Xem
  `packages/ingest/math9_ingest/adapters/README.md`.

**Việc tiếp theo:** khi có link nguồn → viết adapter (~40-60 dòng/nguồn).

---

## methods ✅

Tái tổ chức tài liệu thành sổ tay theo goal_type. Chạy được, có test.

**Đã xong:** schema sổ tay, bản đồ dạng-bài → goal_type cho tài liệu toanmath,
tách tài liệu theo mục, pipeline LLM soạn nháp, xuất khung + checklist soát,
cổng chặn RAG.

**Còn thiếu:**
- 🔲 Nối LLM thật trong `Reorganizer` (hiện có khung, cần API key).
- 🔲 Bản đồ section cho tài liệu nguồn khác (nếu dùng thêm nguồn ngoài toanmath).

**Việc tiếp theo:** chạy trên text đã OCR của tài liệu toanmath → sinh draft →
giáo viên soát.

---

## core ✅

ProblemState và orchestrator chạy end-to-end với LLM thật.

**Đã xong:** `ProblemState` (có `Step.predicate`), orchestrator (đồ thị cố định,
vòng lặp giới hạn 2, Solver∥Draftsman song song, RAG, Draftsman dựng thêm điểm
phụ mà Solver dùng), `build_pipeline()` dựng từ `.env`, `OpenAICompatClient`
(OpenAI hoặc vLLM local), test pipeline với LLM giả.

**Còn thiếu:**
- 🔲 `MODEL_POLICY` chưa có hiệu lực — mọi agent dùng một model (`MODEL_NAME`)
  vì chưa có model local. Khi có vLLM, bỏ tham số `model=` trong `build_pipeline`.
- ✅ Tracing Langfuse (`tracing.py`): mỗi lượt giải một trace `giai-bai`; span cho từng agent, RAG,
  verifier (WARNING khi không qua), `giai-lai` kèm lý do; generation cho mỗi lượt gọi LLM (prompt, kết quả,
  token, chi phí). Ảnh đề không gửi lên, chỉ ghi tên + dung lượng. Không có khóa/thư viện thì tự tắt;
  test đặt `LANGFUSE_TRACING=0`.
- 🔲 Cache kết quả theo hash đề bài.

---

## agents ✅

| Agent | Trạng thái | Ghi chú |
|---|---|---|
| Parser | ✅ | Ảnh → đề bài bằng VLM; từ chối ảnh không phải đề toán |
| Router | ✅ | Chấm được bằng eval (`router_accuracy`) |
| Solver | ✅ | Xuất `predicate` mỗi bước + `algebra_checks` cho SymPy |
| Draftsman | ✅ | Vòng lặp nội bộ 2 lượt; nhận feedback điểm phụ từ lời giải |
| Critic | ✅ không LLM | Tổng hợp phản hồi Verifier thành `retry_feedback` |
| Pedagogue | ✅ | Gợi ý Socratic, chỉ chạy khi confidence ≠ low |

**Lưu ý đã học từ chạy thật:** LLM hay viết LaTeX (`\frac`, `\sqrt`) trong
JSON → `Agent.parse_json` tự sửa; prompt yêu cầu ký hiệu Unicode. Bài trắc
nghiệm trong eval phải kèm đủ 4 phương án, không thì hệ thống trả LOW (đúng).

**Việc tiếp theo:** đọc báo cáo eval, sửa prompt theo trục sai nhiều nhất.

---

## exam ✅

Luyện đề thi vào 10. Chạy được, có test (`tests/test_exam.py`), không cần LLM.

**Đã xong:**
- **Kho bài thật** (`bank.py`): đọc các bài theo chương trình GDPT 2018 trong `data/eval/`, bỏ bài
  vượt chương trình và bài chương trình cũ, gộp các ý a/b/c của cùng một bài theo `context_id`.
  Bài chứng minh để học sinh tự chấm; bài tính ra đáp số thì chấm tự động.
- **Biến thể đổi số** (`variants.py`): 13 mẫu cho bài tính toán (bất phương trình, phương trình
  bậc hai, hệ phương trình, Viète, parabol, tham số, căn thức, lập hệ, xác suất, tần số tương đối,
  tỉ số lượng giác, thể tích). Đáp án tính bằng số học chính xác; test giải lại **độc lập** bằng
  SymPy trên 60 hạt giống mỗi mẫu. Bài hình chứng minh không làm biến thể.
- **Cấu trúc đề** (`data/exam/blueprints.yaml`): 6 tỉnh (Hà Nội, TP.HCM, Nghệ An, Thanh Hóa,
  Quảng Ninh, Hà Tĩnh), suy ra từ đề 2026 trong kho. Có thêm chế độ tự chọn chuyên đề, số câu
  và mức độ.
- **Chấm** (`grading.py`): trắc nghiệm, đúng/sai (thang 10/25/50/100%), trả lời ngắn, tự luận có
  đáp số (so bằng SymPy, có xét dấu bất đẳng thức và thứ tự nghiệm). Bộ so đáp án dùng chung với
  eval, đặt ở `math9_verifier.answer`.
- **API** `/api/exam`: đáp án chỉ nằm trên server (bảng `exam_attempts`, gắn với người tạo đề). Trình
  duyệt chỉ nhận đáp án sau khi nộp bài.
- **Web** `/exam`: đồng hồ đếm ngược (hết giờ tự nộp), lưu bài đang làm khi tải lại trang, tự chấm
  câu chứng minh, "làm lại đề này" (cùng seed ra cùng đề), "xem lời giải chi tiết" mở trang Giải bài
  với đề điền sẵn. Đã kiểm tra trong Edge headless (`frontend/e2e/browser_exam_check.mjs`).

- **Hình của đề** (`figures.py`, `data/exam/figures.yaml`): bài nói "như hình vẽ", "biểu đồ..." có
  hình do server vẽ ra SVG (biểu đồ cột, đoạn thẳng, ghép nhóm, quạt, đồ thị parabol, hình học bằng
  engine dựng hình). Bài nhắc tới hình mà chưa có mục trong `figures.yaml` thì **tự bị loại khỏi
  đề**; test báo tên bài thiếu hình. Nhập đề mới có hình thì thêm mục vào file này.

- **Kho đề Qdrant** (`index.py`, `intake.py`, trang `/admin`): tải PDF/Word/ảnh đề lên → LLM tách bài,
  **chép đáp án có sẵn trong tài liệu, không tự giải**, kèm đoạn trích làm bằng chứng → kiểm tra (đủ 4
  phương án, chuyên đề, trùng với kho bằng hash + độ giống ≥ 0,95, cần hình) → người duyệt sửa/duyệt
  → Qdrant. Bài đã duyệt tự vào kho luyện đề (`load_bank`) và API `GET /api/similar` (không trả đáp án).
  Embedding `text-embedding-3-small`; tên collection gắn theo model. Trang quản trị chỉ tài khoản admin vào được.
  Kiểm tra: `tests/test_problem_index.py`, `frontend/e2e/browser_admin_check.mjs`.

**Lưu ý dữ liệu:** kho luyện đề dùng chung bài với bộ eval. **Không bao giờ** nạp bài trong kho,
hay lời giải sinh ra khi học sinh bấm "xem lời giải", vào RAG (`data/problems/`). Nếu làm vậy,
Solver sẽ thuộc đáp án và điểm eval không còn ý nghĩa.

**Còn thiếu:**
- 🔲 Giáo viên xác nhận **điểm từng ý và thời gian** trong `blueprints.yaml` (hiện là ước lượng,
  tổng luôn 10).
- 🔲 Kho bài hình chứng minh nhỏ: chỉ khoảng 9 bài hình nhiều ý — tăng dần bằng cách tải đề lên `/admin`.
- 🔲 Đính kèm hình cho bài tải lên (hiện bài cần hình bị loại khỏi đề luyện).
- 🔲 Chuyển Qdrant cục bộ lên Qdrant Cloud (chờ URL + API key).
- 🔲 Đúng/Sai chỉ có 2 bài; chưa có biến thể cho dạng này.
- 🔲 Lịch sử làm bài, thống kê chuyên đề yếu (cần đăng nhập).
- 🔲 Chấm bài chứng minh từ ảnh bài làm (dùng VLM + Verifier).

---

## accounts ✅

Tài khoản học sinh + lịch sử. PostgreSQL trên Supabase (SQLAlchemy 2 + psycopg 3); test dùng SQLite
trong bộ nhớ (`tests/test_accounts.py`), kiểm tra trình duyệt `frontend/e2e/browser_auth_check.mjs`.

**Đã xong:**
- Một tài khoản admin duy nhất (`tools/create_admin.py`, `--reset` khi quên mật khẩu); không có tự đăng ký.
  Admin tạo tài khoản học sinh ở `/admin` → Học sinh (dán danh sách tên, mật khẩu tạm tự sinh, in phát
  cho lớp), đặt lại mật khẩu, khóa/mở khóa. Mật khẩu do admin cấp phải đổi ở lần đăng nhập đầu (chặn ở server).
- Đăng nhập bằng tên đăng nhập + mật khẩu (không email — chỉ lưu tên đăng nhập, tên hiển thị,
  mật khẩu băm scrypt). Sai 5 lần liên tiếp -> khóa 15 phút; thông báo lỗi không lộ tên đăng nhập nào có thật.
- Phiên 30 ngày trong cookie HttpOnly + SameSite=Lax; bảng phiên chỉ lưu băm của mã. Đổi mật khẩu thì
  đăng xuất mọi máy khác. Kiểm tra trình duyệt: `frontend/e2e/browser_admin_users_check.mjs`.
- Bắt buộc đăng nhập cho giải bài, tải ảnh, luyện đề, gợi ý tương tự, lịch sử. Hạn mức `SOLVE_DAILY_LIMIT`
  bài/ngày (giờ VN); lượt lỗi cũng tính (vẫn tốn lượt gọi model).
- Lịch sử bài đã giải (`solve_records`: đề, ảnh đề chép sang `data/user_images/`, ProblemState đầy đủ) và
  đề đã luyện (`exam_attempts`: đề kèm đáp án — chỉ server đọc, bài làm, kết quả, điểm tự chấm). Mọi truy
  vấn lọc theo user_id; đề gắn người tạo — người khác có mã đề cũng không mở/nộp được.

- Hỏi đáp sau khi giải (`math9_core/tutor.py`, `prompts/tutor.md`, route `/api/chat/{solve_id}`, bảng
  `chat_messages`): trả lời thẳng, stream (chữ đầu ~1–2 s), ngữ cảnh là đúng bài đã giải (các bước, căn cứ,
  kết quả kiểm chứng) + toàn bộ công cụ chương trình, MỖI công cụ gắn sẵn chương của nó (tránh gán nhầm
  chương của bài cho định lí). Nhắc "[bước a2]" -> giao diện tô sáng bước đó trên hình. Câu trả lời không
  qua Verifier (ghi rõ trên giao diện). Giới hạn 15 câu/bài, 100 câu/ngày. Test: `tests/test_chat.py`,
  `frontend/e2e/browser_chat_check.mjs`.

**Còn thiếu:**
- 🔲 Dẫn chứng tới cấp BÀI SGK: cần mục lục SGK Toán 9 KNTT (2 tập) để thêm trường `sgk: {chuong, bai, ten}`
  cho 112 công cụ trong `data/curriculum/*.yaml` — hiện chỉ dẫn tới cấp chương.
- 🔲 Kiểm tra phép tính trong câu trả lời hỏi đáp bằng SymPy (hiện chưa kiểm).
- 🔲 Alembic migration (hiện `create_all` — đổi cấu trúc bảng về sau cần migration).
- 🔲 Ảnh đề trong lịch sử đang nằm trên ổ đĩa server — lên production nên chuyển sang Supabase Storage.
- 🔲 Vai trò giáo viên/phụ huynh xem tiến độ học sinh; thống kê chuyên đề yếu.
- 🔲 Chính sách dữ liệu cho học sinh dưới 16 tuổi (Nghị định 13/2023: cần đồng ý của cha mẹ/người giám hộ).

---

## api + web ✅ (MVP)

**Đã xong:** FastAPI dựng Pipeline một lần khi khởi động; `POST /api/solve`
stream SSE theo giai đoạn (kể cả lần giải lại và lý do) rồi trả `done` với
ProblemState; `GET /api/topics`. Frontend Next.js 15: nhập đề, tiến trình, gợi ý
trước – lời giải sau, nhãn độ tin cậy kèm lý do, hình SVG **tô sáng theo bước**
(engine bọc mỗi đối tượng trong `<g data-name data-pts>`). Đã kiểm tra golden
path trong Edge headless qua CDP (`frontend/e2e/browser_check.mjs`).

```bash
make api    # :8000
make web    # :3000
```

Đầu vào ảnh: `POST /api/upload` (multipart, ≤12 MB, kiểm chữ ký file, trả
`image_id`; client KHÔNG gửi đường dẫn — tránh path traversal) rồi `/api/solve`
với `image_id`. Frontend: chọn file, kéo-thả, dán Ctrl+V.

**Còn thiếu:**
- 🔲 MathLive (bàn phím toán ảo cho mobile), JSXGraph tương tác.
- 🔲 Đăng nhập, lịch sử bài, giới hạn tần suất.
- 🔲 Production: `RAG_REQUIRE_REVIEWED=1`, `CORS_ORIGINS`, Docker.
