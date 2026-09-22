# Tái tổ chức sổ tay phương pháp

Biến tài liệu tra cứu tổ chức **theo dạng bài** thành sổ tay tổ chức **theo
mục tiêu chứng minh** (`goal_type`) — dạng mà Router truy xuất được.

```
tài liệu PDF → ingest+OCR → split_source → section_map → reorganize (LLM)
             → sổ tay draft → giáo viên soát → gate_for_rag → data/methods/
```

## Vì sao phải tái tổ chức, không dùng thẳng

Tài liệu tra cứu tổ chức để **người** tra: mục "Đường tròn", mục "Góc với đường
tròn". Nhưng khi Router xác định `goal_type = prove_concyclic` và cần nạp chiến
lược, nó không có một mục duy nhất để lấy — nguyên liệu nằm rải trong 2–3 mục.
Ngược lại, một mục như "Đường tròn" trộn nhiều mục tiêu (tính độ dài, tiếp
tuyến, đồng viên), nạp cả cụm thì phần lớn là nhiễu.

Quan hệ giữa dạng bài và goal_type là **nhiều-nhiều**. `section_map.py` mã hóa
quan hệ đó; `invert()` lật nó để gom nguyên liệu về từng goal_type.

Ví dụ thực tế với tài liệu "Cẩm nang toanmath 59 trang":
- `prove_concyclic` ← Dạng 29 + Dạng 30
- Dạng 30 ("mô hình mẫu") → nuôi 8 goal_type khác nhau

## Ranh giới: LLM rút, KHÔNG bịa

LLM chỉ rút những gì **có trong tài liệu**: các hướng giải, dấu hiệu nhận biết,
các bước. Hai trường quan trọng nhất để TRỐNG cho giáo viên:

- **Khi nào KHÔNG dùng** hướng này
- **Bẫy thường gặp**

Vì tài liệu tra cứu (và cả lời giải mẫu) không ghi lại những ngả cụt và quyết
định đã loại bỏ. Bịa ra hai mục này nguy hiểm hơn để trống — nó có thể đẩy
Solver đi sai hướng, đúng cái sổ tay sinh ra để tránh.

## Cổng chặn RAG

`gate_for_rag()` chỉ cho sổ tay `status: reviewed` (đã điền đủ hai mục trên)
vào vector search. Bản draft KHÔNG được dùng. Đây là bảo hiểm: sổ tay nửa vời
còn tệ hơn không có sổ tay.

## Quy trình

```bash
# 1. Xem tài liệu phủ được gì (không cần text)
python tools/build_methods.py --map cam_nang_toanmath --coverage-only

# 2. Trích text (công thức tài liệu này VỠ khi trích thẳng — phải qua Mathpix)
#    dùng tầng ingest: extract + ocr

# 3. Sinh khung draft
python tools/build_methods.py --source-text data/raw/cam-nang.txt \
    --map cam_nang_toanmath --use-llm --out data/methods_draft

# 4. Giáo viên mở từng .md, điền 2 mục để trống, gắn bài minh họa, đổi status
# 5. Nghiệm thu: chỉ file reviewed mới vào data/methods/ chính thức
```

## Chi phí giáo viên

Không có tài liệu này: viết 40–60 sổ tay từ đầu, ~4 tuần.
Có tài liệu này: soát và bổ sung 2 mục, ~1 tuần.

Tài liệu càng đầy đủ, bước LLM rút càng tốt, giáo viên càng nhẹ. Nhưng bước
soát không bỏ được — nó là chỗ đưa vào tri thức mà không tài liệu nào có.

## Bản quyền

Tài liệu bên thứ ba (toanmath và tương tự) dùng làm **nguyên liệu để soạn lại**,
không nhét nguyên văn vào RAG. Sổ tay đầu ra là văn bản do bạn và giáo viên
viết mới, tổ chức lại theo goal_type, có bổ sung — không phải bản sao. Trường
`provenance` ghi nguồn để truy vết, không phải để tái phân phối.
