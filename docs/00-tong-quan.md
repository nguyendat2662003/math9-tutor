# 00 — Tổng quan trạng thái dự án

Điểm vào cho toàn bộ tài liệu công việc. Đọc file này trước.

## Dự án là gì

Chatbot giải toán lớp 9 (Đại số + Hình học) bám chương trình GDPT 2018, có vẽ
hình chính xác, có kiểm chứng đáp án, bám cách trình bày của học sinh Việt Nam.

## Bản đồ tài liệu

| File | Dành cho ai | Nội dung |
|---|---|---|
| `00-tong-quan.md` | Tất cả | File này — trạng thái, cách đọc |
| `01-kien-truc.md` | Kỹ sư | Bốn nguyên tắc, luồng xử lý, 8 package |
| `02-cong-viec-theo-package.md` | Kỹ sư | Từng package: xong gì, thiếu gì, làm sao |
| `03-lo-trinh-sprint.md` | Quản lý | 12 sprint, đầu ra từng sprint |
| `04-cong-viec-giao-vien.md` | Giáo viên | Bản đồ chương trình, sổ tay, chấm eval |
| `05-du-lieu-va-rag.md` | Kỹ sư dữ liệu | Kho dữ liệu nào, vào đâu, vì sao |
| `06-danh-gia.md` | Tất cả | Bộ eval, chỉ số, ngưỡng nghiệm thu |
| `07-rui-ro.md` | Quản lý | Rủi ro và cách giảm thiểu |
| `08-bat-dau-tu-dau.md` | Tất cả | Việc tuần đầu — làm trước khi code |

## Trạng thái hiện tại (bản scaffold)

Toàn bộ phần **không phụ thuộc LLM** đã chạy được và có test. Đây là phần lõi,
cũng là tài sản thật của dự án.

| Thành phần | Trạng thái | Test |
|---|---|---|
| Engine dựng hình (`geometry`) | ✅ Chạy được | ✅ |
| Verifier hình học + đại số (`verifier`) | ✅ Chạy được | ✅ |
| Guardrail chương trình (`curriculum`) | ✅ Chạy được | ✅ |
| Nhập dữ liệu (`ingest`) | ✅ Chạy được | ✅ |
| Tái tổ chức sổ tay (`methods`) | ✅ Chạy được | ✅ |
| Tầng RAG (`retrieval`) | ✅ Chạy được | ✅ |
| `ProblemState` + orchestrator (`core`) | ✅ Chạy end-to-end | ✅ (LLM giả) |
| 6 agent (Parser…Pedagogue) | ✅ Router/Solver/Draftsman/Critic/Pedagogue chạy với LLM thật; Parser ảnh 🔲 | ✅ |
| Bộ eval (`evals/run.py`) | ✅ Chấm tự động 5 chỉ số, có baseline smoke | — |
| Demo Streamlit (`apps/demo_streamlit.py`) | ✅ Giải toán + dựng hình | ✅ AppTest |
| API + frontend Next.js | 🔲 Khung + tầng dữ liệu | — |

53 test đều xanh, chạy `make test` (~1 giây). Chạy thử: `make ui` (Streamlit)
hoặc `python tools/solve.py "<đề bài>"`.

## Ba việc lớn còn lại

1. **Giáo viên soát nội dung** — 26 sổ tay, 10 file chương trình, bài mẫu do
   máy sinh (`data/problems/`). Chưa soát thì RAG không nạp. Ở `04`.
2. **Nâng chất lượng theo eval** — chạy `python evals/run.py --set smoke` sau
   mỗi thay đổi prompt; xem báo cáo trong `evals/reports/`. Ở `06`.
3. **Sản phẩm người dùng** — API nối Pipeline (SSE), frontend Next.js với ba
   yêu cầu sư phạm. Ở `02`.
