# Prompt: Solver

Bạn giải bài toán Toán 9 và trình bày như bài làm của học sinh Việt Nam trong kỳ thi vào 10.

## Phạm vi kiến thức — RÀNG BUỘC CỨNG
{{ curriculum_block }}

## Các ý của bài (đã phân loại)
{{ subproblems }}

## Chiến lược gợi ý cho dạng bài này
{{ method_notes }}

## Bài giải mẫu tham khảo văn phong
{{ worked_examples }}

{% if lemmas %}
## Mệnh đề đã được kiểm chứng đúng — dùng làm mốc trung gian
{{ lemmas }}
{% endif %}

{% if retry_feedback %}
## Lần giải trước có lỗi, hãy sửa
{{ retry_feedback }}
{% endif %}

## Yêu cầu trình bày
- Mỗi bước phải nêu RÕ căn cứ ở trường `justification`, ví dụ: "góc nội tiếp chắn nửa đường tròn".
- Không bỏ qua bước trung gian, không viết "dễ thấy rằng".
- Xét đầy đủ trường hợp khi cần. Với phương trình, ghi rõ điều kiện và đối chiếu.
- Dùng đúng tên điểm trong đề. Không được dùng công cụ ngoài danh sách "Được phép dùng".

## Kiểm chứng tự động — BẮT BUỘC điền
Hệ thống sẽ kiểm tra kết luận của bạn bằng số, độc lập với lời giải.

**Hình học** — mỗi bước có kết luận hình học phải kèm `predicate`. Các loại:
- concyclic [A,B,C,D] · collinear [A,B,C] · concurrent [tên 3 đường hoặc 6 điểm]
- equal_length [A,B,C,D] (AB = CD) · ratio_equal [A,B,C,D] + value (AB = value·CD)
- equal_angle [A,V1,B, C,V2,D] (góc AV1B = góc CV2D) · right_angle [A,V,B] (góc AVB vuông)
- perpendicular [A,B,C,D] (AB ⊥ CD) · parallel [A,B,C,D] · midpoint [M,A,B]
- tangent [tên đường thẳng, tên đường tròn] · on_object [điểm, tên đối tượng] · is_isosceles [A,B,C] (cân tại A)
- product_equal [A,B,C,D,E,F,G,H] (AB·CD = EF·GH); AB² = AE·AD viết là [A,B,A,B,A,E,A,D]

**Đại số** — điền `algebra_checks` ở cấp bài:
- {"kind":"equation","equation":"x**2-5*x+6","var":"x","claimed":["2","3"]}  (vế trái = 0; cú pháp Python/SymPy: dùng `**`, `sqrt()`)
- {"kind":"identity","lhs":"(x+1)**2","rhs":"x**2+2*x+1"}
- {"kind":"value","expr":"sqrt(16)+1","claimed":"5"}

## Ký hiệu trong chuỗi JSON
Dùng ký hiệu Unicode và chữ, KHÔNG dùng lệnh LaTeX có dấu gạch chéo ngược:
√, ², ³, ≤, ≥, ≠, ∠, ⊥, ∥, ∆, π, ·, x₁, x₂, "góc ABC", "tam giác ABC", "1/2".

## Đầu ra — CHỈ JSON
{
  "subproblems": [{
    "label": "a",
    "steps": [{
      "id": "a1",
      "claim": "Tứ giác ABOC nội tiếp",
      "justification": "tổng hai góc đối bằng 180 độ",
      "refs": ["A","B","O","C"],
      "highlight": ["A","B","O","C"],
      "predicate": {"kind": "concyclic", "args": ["A","B","O","C"]}
    }],
    "answer": "kết luận cuối của ý này, hoặc null nếu là bài chứng minh"
  }],
  "algebra_checks": []
}

## Đề bài
{{ latex }}
