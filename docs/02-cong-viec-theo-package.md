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

## agents ✅ (trừ Parser ảnh)

| Agent | Trạng thái | Ghi chú |
|---|---|---|
| Parser | 🔲 ảnh | Text đi thẳng; ảnh chưa nối OCR/VLM |
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

## api + web 🔲

**Đã xong:** khung FastAPI, endpoint solve (stream), SSE, tầng dữ liệu frontend
(types, client SSE).

**Còn thiếu:**
- 🔲 Nối Pipeline vào endpoint (chờ agent).
- 🔲 UI: chat, MathLive input, solution-view, JSXGraph figure.
- 🔲 Ba yêu cầu đặc thù: hình đồng bộ bước giải, chế độ gợi ý mặc định, nhãn
  độ tin cậy. Xem `apps/web/README.md`.

**Việc tiếp theo:** làm sau khi có Pipeline chạy được end-to-end.
