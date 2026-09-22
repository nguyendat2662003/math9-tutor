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
| `ProblemState` + orchestrator (`core`) | ⚙️ Khung đầy đủ | — |
| 6 agent (Parser…Pedagogue) | 🔲 Stub + prompt | — |
| API + frontend | 🔲 Khung + tầng dữ liệu | — |

37 test đều xanh, chạy `make test` (~0.4 giây).

## Ba việc lớn còn lại

1. **Sáu agent** — cần API key, cần prompt hoàn chỉnh. Chi tiết ở `02`.
2. **Bộ eval + baseline** — việc tuần đầu, làm TRƯỚC khi viết agent. Ở `08`.
3. **Nội dung của giáo viên** — bản đồ chương trình, sổ tay. Ở `04`.

## Vì sao agent để stub có chủ đích

Viết prompt Solver trước khi biết model sai ở trục nào là đầu tư sai chỗ. Bộ
eval tuần đầu (`08`) sẽ cho biết chính xác cần ưu tiên gì. Xây lõi kiểm chứng
trước, agent sau, là thứ tự đúng.
