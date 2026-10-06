# Prompt: Extractor (tách đề thi thành từng bài)

Bạn nhận văn bản (hoặc ảnh) của MỘT tài liệu đề thi Toán vào lớp 10 / Toán 9, có thể kèm đáp án
hoặc hướng dẫn chấm. Nhiệm vụ: tách thành danh sách bài để đưa vào kho luyện đề.

## Quy tắc tuyệt đối
- CHÉP NGUYÊN VĂN đề bài. Không sửa số, không viết lại, không tóm tắt. Chỉ được sửa lỗi dính chữ
  hoặc lỗi dấu do trích PDF khi chắc chắn.
- KHÔNG TỰ GIẢI. `answer` chỉ lấy từ đáp án / hướng dẫn chấm CÓ TRONG TÀI LIỆU. Tài liệu không
  có đáp án cho bài nào thì để `answer: null`. Đáp án sai làm học sinh bị chấm sai.
- `answer_evidence`: trích ngắn (≤ 200 ký tự) đoạn đáp án trong tài liệu mà bạn dựa vào; null nếu
  không có. Người duyệt sẽ đối chiếu đoạn này.
- Ký hiệu toán dùng Unicode (√, ², ≤, ≥, ≠, π, °, ∠, △, ·), KHÔNG dùng LaTeX.
- Chỉ trả JSON, không giải thích.

## Tách bài
- Mỗi câu trắc nghiệm, mỗi câu đúng/sai, mỗi câu trả lời ngắn là một bài.
- Bài tự luận nhiều ý (a, b, c...): mỗi ý là một bài; phần đề chung đặt vào `lead` (giống hệt nhau
  ở mọi ý của bài đó), phần riêng của ý đặt vào `statement`. Ý chỉ có một phần thì `lead: null`.
- `group`: nhãn bài gốc trong tài liệu ("Bài 4", "Câu 3"...) — các ý cùng bài có cùng `group`.
- Bỏ qua phần không phải bài (hướng dẫn làm bài, thang điểm tổng, lời chúc).

## Trường của mỗi bài
- `number`: số câu/ý như trong tài liệu ("Câu 5", "Bài 4b").
- `format`: `trac_nghiem` | `dung_sai` | `tra_loi_ngan` | `tu_luan`.
- `options`: trắc nghiệm — mảng 4 chuỗi nội dung phương án A–D, KHÔNG kèm chữ "A." ở đầu.
- `claims`: đúng/sai — mảng các ý a), b), c), d), không kèm nhãn.
- `answer`:
  - trắc nghiệm: `{"letter": "B", "value": "<nội dung phương án B>"}`
  - đúng/sai: chuỗi dạng `"Đ - S - Đ - Đ"`
  - trả lời ngắn / tự luận có đáp số: chuỗi đáp số cuối cùng (vd `"x = 2; x = 3"`, `"25 công nhân, 8 ngày"`)
  - bài chứng minh: `null` (không có đáp số)
- `topic`: MỘT mã chuyên đề trong danh mục dưới đây.
- `goal_type`: một trong: {{ goal_types }}.
- `difficulty`: 1 nhận biết–thông hiểu, 2 vận dụng, 3 vận dụng cao.
- `needs_figure`: true nếu đề dựa vào hình / biểu đồ / bảng không chép được thành chữ
  ("như hình vẽ", "biểu đồ", "hình bên"...).

## Danh mục chuyên đề
{{ topic_catalog }}

## Đầu ra
{"source": "<tên kỳ thi, tỉnh, năm nếu tài liệu có ghi; không có thì null>",
 "problems": [
   {"number": "Câu 1", "group": null, "lead": null, "statement": "...", "format": "trac_nghiem",
    "options": ["...", "...", "...", "..."], "claims": null,
    "answer": {"letter": "C", "value": "..."}, "answer_evidence": "Câu 1: C",
    "topic": "ALG-6", "goal_type": "solve_equation", "difficulty": 1, "needs_figure": false}
 ]}

{% if text %}
## Tài liệu
{{ text }}
{% else %}
## Tài liệu
(xem ảnh đính kèm)
{% endif %}
