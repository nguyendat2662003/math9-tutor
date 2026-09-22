# 01 — Kiến trúc

## Bốn nguyên tắc

**1. Đồ thị cố định, không ủy quyền động.**
Toán lớp 9 là miền đóng, quy trình xử lý một bài luôn giống nhau. Không agent
nào tự quyết gọi agent khác. Debug được, đo được, chi phí dự đoán được. Tránh
các framework agent tự chủ (CrewAI, AutoGen) — chúng tối ưu cho việc agent tự
thương lượng, thứ ta không cần.

**2. LLM không bao giờ sinh tọa độ.**
LLM sinh *kịch bản dựng hình* khai báo; engine tính tọa độ bằng công thức toán
học. Nếu để LLM tự đặt tọa độ, hình sẽ sai quan hệ — điểm không nằm trên đường
tròn, tam giác vuông thành tù. Đây là chỗ đa số dự án tương tự thất bại.

**3. Kiểm chứng bằng code, không bằng LLM.**
Nếu để một LLM kiểm tra lời giải của LLM khác, hai bên sai giống nhau. Giá trị
nằm ở dùng cơ chế độc lập: SymPy giải lại đại số, engine dựng lại hình 5 lần
với cấu hình ngẫu nhiên và kiểm tra vị từ bằng số.

**4. Thà thừa nhận không chắc còn hơn trả lời sai.**
Vòng lặp Solver ↔ Verifier giới hạn cứng 2 lần. Sau đó trả về phần đã chắc
chắn kèm nhãn `confidence`. Trả lời sai một cách tự tin cho học sinh là lỗi tệ
nhất mà sản phẩm có thể mắc.

## Luồng xử lý

```
Parser → Router → RAG → { Solver ∥ Draftsman } → Verifier → [Critic] → Render → Pedagogue
                              ↑                       │
                              └──── giải lại (tối đa 2) ┘
```

- **Parser** chỉ chạy khi đầu vào là ảnh.
- **RAG** nạp sổ tay chiến lược (theo goal_type) và bài mẫu vào state.
- **Solver và Draftsman chạy song song** — cả hai chỉ cần đề đã chuẩn hóa,
  tiết kiệm ~40% độ trễ.
- **Verifier đối chiếu chéo** hai đầu ra: lời giải nhắc điểm K mà hình không có
  K → một trong hai hiểu sai đề.
- **Critic** chỉ chạy khi Verifier báo nghi ngờ.
- **Pedagogue** chuyển lời giải thành gợi ý từng bước.

## Thang leo thang theo độ khó

| Mức | Chiến lược | Độ trễ | Lưu lượng |
|---|---|---|---|
| 1 quen thuộc | Một lượt gọi, verify | < 12s | ~75% |
| 2 khó vừa | Nạp sổ tay, sinh 3 lời giải, Verifier chọn | < 35s | ~20% |
| 3 rất khó | Hai pha: giải tự do → dò bổ đề → hạ về công cụ lớp 9 | < 90s | ~5% |

### Kỹ thuật hai pha (mức 3)

Phần khó nhất của bài hình là *đoán được cần chứng minh gì*, không phải chứng
minh nó. Nên:

1. **Giải tự do** — cho phép mọi công cụ (tọa độ, lượng giác, phương tích), chỉ
   để tìm ra đáp án và đường đi.
2. **Dò bổ đề** — engine quét tự động tập vị từ trên hình đã dựng; mệnh đề đúng
   trên cả 5 cấu hình là bổ đề thật.
3. **Hạ cấp** — Solver chứng minh lại bằng công cụ lớp 9, dùng bổ đề làm mốc.
   Bài khó bị bẻ thành chuỗi bài dễ.

## Object trạng thái duy nhất

Điểm chết của multi-agent là mất ngữ cảnh khi truyền qua lại. Cách chữa: mọi
agent đọc và ghi vào một `ProblemState` duy nhất, không nhận text thô từ agent
trước. Xem `packages/core/math9_core/state.py`.

## Tám package

| Package | Vai trò | LLM? |
|---|---|---|
| `geometry` | DSL, engine dựng hình, ràng buộc số, layout, render SVG | Không |
| `verifier` | Vị từ, kiểm chứng hình, SymPy, dò bổ đề | Không |
| `curriculum` | Schema chương trình, guardrail 2 lớp | Không |
| `retrieval` | RAG hybrid, 3 collection tách biệt | Embedder |
| `ingest` | Crawl, trích xuất, chuẩn hóa, khử trùng lặp | OCR |
| `methods` | Tái tổ chức tài liệu thành sổ tay theo goal_type | LLM (soạn nháp) |
| `core` | ProblemState, orchestrator, agent, chính sách model | Có |
| (agents) | Parser, Router, Solver, Draftsman, Critic, Pedagogue | Có |

Bốn package đầu hoàn toàn không cần LLM — kiểm thử tất định, là tài sản lõi.
