# 03 — Lộ trình sprint

Sprint 2 tuần. Cột "trạng thái" đánh dấu phần scaffold đã có sẵn.

| Sprint | Mục tiêu | Đầu ra | Đã có sẵn |
|---|---|---|---|
| 0 | Nền tảng đo lường | Bộ eval 200 bài, baseline model API. **Chưa viết sản phẩm** | Khung eval |
| 1 | Bản đồ chương trình | 10 file YAML (KNTT), guardrail chạy trên 100 lời giải mẫu | Code guardrail ✅, 10/10 file (chờ soát) |
| 2–3 | MVP đại số | Chat + KaTeX + Solver + Verifier SymPy, đạt ngưỡng Core (ALG) | Verifier ✅, Solver stub |
| 4–5 | Engine hình học | DSL, engine, layout, render — đạt ngưỡng Figure | **Toàn bộ ✅** |
| 6–7 | Hình học end-to-end | Draftsman, Verifier hình, hình đồng bộ bước giải | Verifier ✅, Draftsman stub |
| 8 | Sổ tay phương pháp | 40+ tài liệu, RAG theo goal_type, đo lại Hard | RAG ✅, pipeline methods ✅ |
| 9 | Bài khó | Thang leo thang, hai pha, dò bổ đề | Dò bổ đề ✅ |
| 10 | Sư phạm | Chế độ gợi ý từng bước, Pedagogue | Stub |
| 11 | Đầu vào ảnh | Parser OCR/VLM | **Xong** — VLM đọc đề từ ảnh, có upload + UI |
| 12 | Tối ưu | Định tuyến model theo độ khó, cache, giảm chi phí | Chính sách model ✅ |

## Ghi chú quan trọng theo sprint

**Sprint 0 quan trọng hơn vẻ ngoài.** Không có bộ eval, mọi thay đổi prompt về
sau đều là đoán mò. Hai tuần này KHÔNG viết sản phẩm — chỉ xây bộ đo và chạy
baseline. Xem `08`.

**Sprint 1 — sổ tay bắt đầu từ ĐÂY, không để cuối.** Đây là phần cần giáo viên
soạn, mất 3-4 tuần (hoặc 1 tuần nếu dùng pipeline tái tổ chức từ tài liệu có
sẵn). Nếu để đến Sprint 8 mới bắt đầu, nó thành đường găng của cả dự án.

**Sprint 4-5 gần như xong sẵn.** Engine hình học — phần được cho là nặng nhất —
đã có đầy đủ trong scaffold. Sprint này chủ yếu là hoàn thiện `export_jsx.py`
và test kỹ trên bài thật.

**Sprint 8 phụ thuộc Sprint 1.** Sổ tay phải đã soát xong mới nạp được vào RAG.
Nếu Sprint 1 chưa xong phần nội dung, Sprint 8 sẽ trượt.

## Đường găng thực sự

Không phải code — mà là **nội dung của giáo viên**:

```
Tìm giáo viên → bản đồ chương trình (17 file) → sổ tay (40+ tài liệu, đã soát)
```

Chuỗi này dài 6-8 tuần và không rút ngắn được bằng cách thêm kỹ sư. Bắt đầu
ngay từ ngày 1. Xem `04`.

## Nhân sự tối thiểu

| Vai trò | Toàn thời gian | Trách nhiệm |
|---|---|---|
| Kỹ sư AI/Backend | 1 | Orchestrator, agent, verifier, engine hình |
| Kỹ sư Frontend | 1 | Web, render công thức/hình, UX sư phạm |
| Giáo viên Toán THCS | 1 (hoặc 2 bán TG) | Chương trình, sổ tay, chấm eval |
| Sản phẩm/điều phối | 0.5 | Ưu tiên, đo lường, làm việc với trường |

Giáo viên là vai trò không thể thay thế. Kỹ sư không tự viết được sổ tay.
