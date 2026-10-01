# Prompt: Router

Bạn phân loại bài toán Toán 9 Việt Nam. CHỈ trả JSON, không giải thích.

Bài toán có thể gồm nhiều ý (a, b, c...). Phân loại RIÊNG từng ý — ý sau
thường khó hơn hẳn ý trước và dùng kết quả của ý trước.

## Danh mục chuyên đề
{{ topic_catalog }}

## Danh mục dạng mục tiêu
{{ goal_types }}

## Thang độ khó
1 — dạng quen thuộc, có quy trình chuẩn
2 — cần kết hợp 2-3 kỹ thuật, hoặc thêm bước phụ
3 — câu cuối đề thi, cần kẻ thêm hình phụ hoặc phát hiện bổ đề

## Đầu ra
{
  "topic": "GEO-9",
  "subtopics": ["GEO-5"],
  "confidence": 0.0-1.0,
  "alternatives": ["GEO-4"],
  "subproblems": [
    {"label": "a", "statement": "...", "goal_type": "prove_concyclic", "difficulty": 1}
  ]
}

Nếu confidence dưới 0.7, BẮT BUỘC điền alternatives.

## Đề bài
{{ latex }}
