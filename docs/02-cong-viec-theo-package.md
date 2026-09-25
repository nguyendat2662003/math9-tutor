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
- 🔲 Nối Mathpix thật trong `extract/ocr.py` (hiện là khung, cần API key).

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
- 🔲 Tracing (Langfuse) — có key trong `.env`, chưa nối.
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
- **API** `/api/exam`: đáp án chỉ nằm trên server (`data/exams/`, tra bằng id ngẫu nhiên, tự xóa
  sau 7 ngày). Trình duyệt chỉ nhận đáp án sau khi nộp bài.
- **Web** `/exam`: đồng hồ đếm ngược (hết giờ tự nộp), lưu bài đang làm khi tải lại trang, tự chấm
  câu chứng minh, "làm lại đề này" (cùng seed ra cùng đề), "xem lời giải chi tiết" mở trang Giải bài
  với đề điền sẵn. Đã kiểm tra trong Edge headless (`demo/browser_exam_check.mjs`).

- **Hình của đề** (`figures.py`, `data/exam/figures.yaml`): bài nói "như hình vẽ", "biểu đồ..." có
  hình do server vẽ ra SVG (biểu đồ cột, đoạn thẳng, ghép nhóm, quạt, đồ thị parabol, hình học bằng
  engine dựng hình). Bài nhắc tới hình mà chưa có mục trong `figures.yaml` thì **tự bị loại khỏi
  đề**; test báo tên bài thiếu hình. Nhập đề mới có hình thì thêm mục vào file này.

**Lưu ý dữ liệu:** kho luyện đề dùng chung bài với bộ eval. **Không bao giờ** nạp bài trong kho,
hay lời giải sinh ra khi học sinh bấm "xem lời giải", vào RAG (`data/problems/`). Nếu làm vậy,
Solver sẽ thuộc đáp án và điểm eval không còn ý nghĩa.

**Còn thiếu:**
- 🔲 Giáo viên xác nhận **điểm từng ý và thời gian** trong `blueprints.yaml` (hiện là ước lượng,
  tổng luôn 10).
- 🔲 Kho bài hình chứng minh nhỏ: chỉ khoảng 9 bài hình nhiều ý, làm vài đề là gặp lại. Nhập thêm đề
  (qua `ingest`) sẽ tăng kho.
- 🔲 Đúng/Sai chỉ có 2 bài; chưa có biến thể cho dạng này.
- 🔲 Lịch sử làm bài, thống kê chuyên đề yếu (cần đăng nhập).
- 🔲 Chấm bài chứng minh từ ảnh bài làm (dùng VLM + Verifier).

---

## api + web ✅ (MVP)

**Đã xong:** FastAPI dựng Pipeline một lần khi khởi động; `POST /api/solve`
stream SSE theo giai đoạn (kể cả lần giải lại và lý do) rồi trả `done` với
ProblemState; `GET /api/topics`. Frontend Next.js 15: nhập đề, tiến trình, gợi ý
trước – lời giải sau, nhãn độ tin cậy kèm lý do, hình SVG **tô sáng theo bước**
(engine bọc mỗi đối tượng trong `<g data-name data-pts>`). Đã kiểm tra golden
path trong Edge headless qua CDP (`demo/browser_check.mjs`).

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
