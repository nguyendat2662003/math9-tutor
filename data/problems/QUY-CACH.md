# Quy cách bài giải mẫu

Bài mẫu phục vụ RAG few-shot cho Solver. Mục tiêu kép: dạy **văn phong trình bày**
và dạy **định dạng đầu ra có cấu trúc**.

## Cách nạp vào hệ thống

Mỗi bài là **một file `*.json` riêng** trong `data/problems/` (không phải một
dòng trong file `.jsonl` chung) — để giáo viên mở, đọc, sửa tay từng bài dễ
dàng, giống hệt cách làm việc với sổ tay phương pháp.

`load_worked_examples()` (`packages/retrieval/math9_retrieval/store.py`) nạp
mỗi file, và tách thành **một bản ghi RAG cho mỗi Ý** (`subproblems[i]`) — vì
mỗi ý mang `goal_type` riêng, đây mới là đơn vị mà RAG cần truy xuất, không
phải cả bài. Tên bản ghi là `<id file>-<label ý>`, ví dụ `mau-hai-tiep-tuyen-a`.

## Bốn thành phần bắt buộc

| Thành phần | Vì sao cần |
|---|---|
| 1. Đề bài | Hiển nhiên |
| 2. Nhãn (`topic`, `goal_type`, `difficulty`) | Không có thì retrieval không biết lấy bài nào |
| 3. Lời giải **cấu trúc hóa theo bước** | Solver xuất JSON, không xuất văn xuôi |
| 4. `predicate` cho mỗi kết luận hình học | Cho phép Verifier kiểm chứng tự động |

Thiếu (2) → bài nằm trong kho nhưng không bao giờ được lấy ra.
Thiếu (3) → model học văn phong nhưng xuất sai định dạng.
Thiếu (4) → không kiểm chứng được, không dùng làm eval được.

## Ba thành phần nên có (không bắt buộc)

- **`solution_prose`** — lời giải văn xuôi nguyên bản, để model học cách diễn đạt tự nhiên.
- **`approach_ref`** — bài này minh họa hướng nào trong sổ tay. Ví dụ `prove_concyclic#huong-1`.
  Nhờ trường này mà sổ tay và bài mẫu liên kết được với nhau.
- **`construction`** — kịch bản dựng hình. Nếu có, bài mẫu dùng luôn được cho Draftsman.

## Phân biệt hai loại lời giải — QUAN TRỌNG

| Loại | `solution_type` | Dùng làm gì |
|---|---|---|
| Lời giải chi tiết (giáo viên soạn) | `detailed` | ✅ Bài mẫu few-shot |
| Hướng dẫn chấm của Sở | `answer_key` | ❌ Chỉ lấy đáp án cho eval |

Hướng dẫn chấm viết cho giám khảo: nén tối đa, rải `0,25đ`, bỏ qua căn cứ vì
giám khảo tự hiểu. Nạp làm few-shot sẽ dạy model viết lời giải KHÔNG nêu căn cứ
— đúng thứ guardrail đang cố chặn. Hệ thống tự loại loại này (xem `load_worked_examples`).

## Cùng một đề, nhiều lời giải là QUÝ

Nếu một bài giải được bằng hai hướng khác nhau, ghi thành hai bản ghi với
`approach_ref` khác nhau. Đây là dữ liệu tốt nhất: nó dạy model rằng có nhiều
đường đi, và giúp Solver chọn hướng phù hợp với ràng buộc chế độ.

## Bao nhiêu bài là đủ

| Mốc | Số bài | Đủ để làm gì |
|---|---|---|
| Tối thiểu | 2–3 bài / goal_type (~60 bài) | RAG few-shot hoạt động |
| Tốt | 5–8 bài / goal_type (~150 bài) | Phủ các biến thể thường gặp |
| Fine-tune | 1000+ | Huấn luyện model local |

Bắt đầu từ mốc tối thiểu. Ưu tiên các goal_type xuất hiện nhiều ở đề vào 10.

## Cách làm bán tự động (tiết kiệm ~70% công)

1. Crawl đề + lời giải chi tiết (tầng `ingest` đã có).
2. **LLM cấu trúc hóa** văn xuôi thành các bước `claim` / `justification`.
3. **LLM đề xuất `predicate`** cho mỗi kết luận hình học.
4. **Verifier kiểm chứng tự động** — dựng hình, kiểm tra predicate trên 5 cấu hình.
   Sai → trả lại hàng đợi soát. Đúng → gần như chắc chắn bước đó chuẩn.
5. Giáo viên chỉ soát những bài Verifier báo nghi ngờ, và soát `justification`
   (Verifier kiểm được kết luận ĐÚNG hay SAI, nhưng không kiểm được căn cứ có
   thuộc chương trình lớp 9 không — việc đó guardrail và giáo viên làm).

Điểm mấu chốt: bước 4 lọc được phần lớn lỗi mà không cần người. Giáo viên chỉ
xử lý phần còn lại.
