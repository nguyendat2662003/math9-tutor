---
goal_type: prove_inequality
title_vi: Chứng minh bất đẳng thức, giải bất phương trình
topics: [ALG-2]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Bất đẳng thức và bất phương trình bậc nhất một ẩn (Chương II)

> ⚠ Nội dung này ở chương trình cũ thuộc lớp 8, GDPT 2018 chuyển xuống lớp 9
> (Bài 5, Bài 6). KHÔNG coi là kiến thức đã biết từ trước.

## Hướng 1 — Giải bất phương trình bậc nhất một ẩn (Bài 6)

**Các bước:** chuyển vế, thu gọn về ax + b > 0 → chia hai vế cho a, ĐỔI CHIỀU
nếu a < 0 → biểu diễn tập nghiệm trên trục số.

**Khi nào KHÔNG dùng:** khi a chứa tham số và có thể bằng 0 — phải xét riêng
trường hợp a = 0 (bất phương trình suy biến).

**Bẫy thường gặp:**
- Quên đổi chiều khi nhân/chia với số âm — lỗi phổ biến NHẤT.
- Chuyển vế mà quên đổi dấu.
- Biểu diễn tập nghiệm trên trục số sai chiều, hoặc nhầm dấu ngoặc tròn/vuông (có lấy bằng hay không).
- Với bất phương trình chứa tham số: quên xét dấu của a.

**Ví dụ:** Giải bất phương trình 3 − 2x > 7. Chuyển vế: −2x > 4. Chia hai vế cho −2 và ĐỔI CHIỀU: x < −2. Tập nghiệm: x < −2.

## Hướng 2 — Dùng tính chất của bất đẳng thức (Bài 5)

**Cần nhớ:** cộng cùng một số vào hai vế thì chiều không đổi; nhân với số dương
chiều không đổi, với số âm ĐỔI CHIỀU; bắc cầu a > b và b > c thì a > c.

**Khi nào KHÔNG dùng:** khi cần nhân/chia hai bất đẳng thức với nhau — phép này
chỉ hợp lệ khi cả hai vế đều dương, nhiều học sinh áp dụng bừa.

**Bẫy thường gặp:**
- Trừ vế theo vế hai bất đẳng thức cùng chiều — KHÔNG hợp lệ.
- Nhân vế theo vế khi có vế âm.
- Bình phương hai vế khi chưa biết dấu (a > b không suy ra a² > b²).

**Ví dụ:** Cho a > b. Chứng minh 3a + 1 > 3b + 1. Từ a > b, nhân hai vế với 3 (số dương, chiều không đổi) được 3a > 3b; cộng 1 vào hai vế được 3a + 1 > 3b + 1.

## Hướng 3 — Xét hiệu hai vế

**Khi nào dùng:** chứng minh A ≥ B — xét A − B và chứng minh không âm.

**Các bước:** biến đổi A − B về tổng các bình phương → kết luận ≥ 0 → chỉ rõ dấu bằng.

**Khi nào KHÔNG dùng:** khi hiệu không đưa được về tổng bình phương — thử Cô-si
hoặc biến đổi tương đương.

**Bẫy thường gặp:**
- Quên chỉ điều kiện dấu bằng xảy ra khi nào — mất điểm.
- Biến đổi tương đương nhưng dùng dấu ⇒ thay vì ⇔ (không kết luận ngược được).
- Bỏ sót điều kiện của biến khi tách bình phương.

**Ví dụ:** Chứng minh a² + b² ≥ 2ab với mọi a, b.
Xét hiệu: a² + b² − 2ab = (a − b)² ≥ 0 với mọi a, b. Vậy a² + b² ≥ 2ab.
Dấu bằng xảy ra khi a = b.

## Hướng 4 — Bất đẳng thức Cô-si cho hai số không âm

**Khi nào dùng:** biểu thức có dạng tổng của hai số dương mà tích không đổi.
Dạng kinh điển: x + 1/x ≥ 2 với x > 0.

**Khi nào KHÔNG dùng:** khi các số có thể ÂM — Cô-si chỉ áp dụng cho số không
âm. Cũng không dùng khi tích hai số không cố định (áp dụng trực tiếp không cho
kết quả có ý nghĩa).

**Bẫy thường gặp:**
- Áp dụng cho số âm.
- Quên kiểm tra điều kiện dấu bằng có xảy ra được không (giá trị làm dấu bằng phải nằm trong miền xác định).
- Chia tách biểu thức sai cách khiến dấu bằng không bao giờ đạt được.


**Ví dụ:** Chứng minh (a + b)(1/a + 1/b) ≥ 4 với a, b > 0.
Theo Cô-si: a + b ≥ 2√(ab) và 1/a + 1/b ≥ 2/√(ab).
Nhân hai bất đẳng thức (các vế đều dương): (a+b)(1/a + 1/b) ≥ 4. Dấu bằng khi a = b.

_Công cụ: T-AM-GM-2_
