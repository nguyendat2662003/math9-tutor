# 05 — Dữ liệu và RAG

Kho dữ liệu nào tồn tại, vào đâu, và vì sao. Đây là chỗ quyết định chất lượng.

## Nguyên tắc vàng: SGK không vào RAG

Model không thiếu kiến thức trong SGK — nó đã biết định lý góc nội tiếp. Cái nó
thiếu là *ràng buộc* (được dùng công cụ nào), và ràng buộc phải là dữ liệu có
cấu trúc để code kiểm tra, không phải văn xuôi để model đọc.

Nhét nguyên SGK vào RAG làm hệ thống tệ đi: retrieval trả về đoạn dẫn nhập hoặc
ví dụ dễ hơn, làm loãng prompt. Chi tiết trong README gốc.

## Bốn kho dữ liệu

| Kho | Nội dung | Vào đâu | Truy xuất kiểu gì |
|---|---|---|---|
| Bản đồ chương trình | Định lý, công thức, ký hiệu | `data/curriculum/*.yaml` | Tra chính xác theo topic, **không qua vector** |
| Sổ tay phương pháp | Chiến lược theo goal_type | `data/methods/*.md` | RAG, goal_type là chính |
| Bài giải mẫu | Lời giải chi tiết | `data/problems/` | RAG, độ tương đồng là chính |
| Bộ eval | Đề + đáp án chuẩn | `data/eval/*.jsonl` | Không truy xuất — để đo |

## Ba collection RAG tách biệt

Package `retrieval` giữ ba collection riêng, không trộn:

**`methods`** — sổ tay. Truy **theo goal_type là chính**. Bạn không tìm "bài
giống", bạn tìm "chiến lược phù hợp". Hai bài từ ngữ gần trùng nhưng khác
goal_type sẽ lấy hai sổ tay khác nhau.

**`worked_examples`** — bài mẫu. Truy **theo độ tương đồng** để bắt chước văn
phong trình bày. Chỉ nhận lời giải chi tiết; hướng dẫn chấm của Sở (cụt lủn,
không nêu căn cứ) bị loại.

**`concepts`** — định nghĩa SGK. Collection RIÊNG, chỉ dùng khi học sinh hỏi
kiến thức ("định nghĩa tứ giác nội tiếp"), không phải khi giải bài.

## Hybrid search

`retrieval` gộp BM25 (khớp từ khóa chính xác, ví dụ tên định lý) với vector
(tương đồng ngữ nghĩa) bằng RRF. Với sổ tay, cả hai chỉ để xếp hạng trong nhóm
cùng goal_type, hoặc cứu vãn khi Router phân loại sai.

## Embedder theo giai đoạn

| Backend | Khi nào |
|---|---|
| HashingEmbedder | Test, kho nhỏ (mặc định hiện tại) |
| LocalEmbedder (bge-m3) | Production — đa ngữ, tiếng Việt tốt |
| API embedding | Chất lượng cao nhất |

Tránh model chỉ tiếng Anh — embed "tứ giác nội tiếp" rất kém.

## Luồng dữ liệu vào

```
Nguồn (đề thi, tài liệu) → ingest (fetch, extract, OCR, normalize, dedupe)
  ├→ accepted.jsonl  → bộ eval / kho bài mẫu
  └→ review.jsonl    → giáo viên soát → gán nhãn → eval hoặc RAG

Tài liệu tra cứu → methods (tái tổ chức theo goal_type)
  → sổ tay draft → giáo viên soát → gate_for_rag → data/methods/
```

## Hai cổng chặn

1. **`gate_for_rag`** (methods) — sổ tay chưa điền "khi nào không dùng" + "bẫy"
   bị chặn.
2. **`load_methods(require_reviewed=True)`** (retrieval) — chỉ nạp `status:
   reviewed`.

Hai cổng nối tiếp: sổ tay nửa vời không lọt vào hệ thống ở bất kỳ đâu.

## Bản quyền

- **Đề thi vào 10 công khai của Sở** — an toàn, dùng thoải mái.
- **SGK, SBT** — tham chiếu để soạn, không số hóa nguyên văn để phân phối.
- **Tài liệu bên thứ ba** (toanmath...) — dùng làm nguyên liệu để tái tổ chức,
  output là văn bản viết mới; không nhét nguyên văn vào RAG.
- **Hướng dẫn chấm** — chỉ lấy đáp án cho eval, không làm few-shot.
