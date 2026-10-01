---
goal_type: analyze_function
title_vi: Hàm số y = ax², đồ thị và tương giao với đường thẳng
topics: [ALG-6]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Hàm số y = ax² (a ≠ 0), đồ thị và tương giao (Bài 18)

## Hướng 1 — Vẽ đồ thị và nhận xét tính chất

**Cần nhớ:** đồ thị là parabol đỉnh O, nhận Oy làm trục đối xứng.
- a > 0: bề lõm hướng lên, y ≥ 0, GTNN là 0 tại x = 0.
- a < 0: bề lõm hướng xuống, y ≤ 0, GTLN là 0 tại x = 0.

**Khi nào KHÔNG dùng bảng giá trị thưa:** khi hệ số a lớn, parabol dốc — cần lấy
thêm điểm gần đỉnh để vẽ đúng dáng.

**Bẫy thường gặp:**
- Lấy quá ít điểm làm parabol méo, hoặc vẽ thành đường gấp khúc.
- Quên tính đối xứng: chỉ cần tính x > 0 rồi lấy đối xứng qua Oy.
- Nhận xét sai chiều biến thiên: hàm nghịch biến khi x < 0 và đồng biến khi x > 0 (với a > 0).

**Ví dụ:** Vẽ đồ thị y = x²/2. Bảng giá trị: x = −4 → y = 8; x = −2 → y = 2; x = 0 → y = 0; x = 2 → y = 2; x = 4 → y = 8. Parabol đỉnh O, bề lõm hướng lên (a = 1/2 > 0), đối xứng qua Oy.

## Hướng 2 — Tìm tọa độ giao điểm của parabol và đường thẳng

**Các bước:** lập phương trình hoành độ giao điểm ax² = mx + n → đưa về bậc hai
→ giải → thay x tìm y.

**Khi nào KHÔNG dùng:** khi đề chỉ hỏi SỐ giao điểm chứ không hỏi tọa độ — lúc
đó chỉ cần xét dấu Δ, không cần giải hết.

**Bẫy thường gặp:**
- Chỉ tìm x mà quên tìm y — đề hỏi TỌA ĐỘ giao điểm.
- Thay x vào nhầm phương trình (nên thay vào phương trình đơn giản hơn).
- Chuyển vế sai dấu khi lập phương trình hoành độ giao điểm.

**Ví dụ:** Tìm tọa độ giao điểm của (P): y = x² và (d): y = 2x + 3.
Phương trình hoành độ giao điểm: x² = 2x + 3 ⟺ x² − 2x − 3 = 0 ⟺ x = 3 hoặc x = −1.
Với x = 3 → y = 9; với x = −1 → y = 1. Hai giao điểm: (3; 9) và (−1; 1).

## Hướng 3 — Biện luận số giao điểm theo tham số

**Quy tắc theo dấu Δ của phương trình hoành độ giao điểm:**
Δ > 0 cắt tại hai điểm phân biệt · Δ = 0 tiếp xúc · Δ < 0 không cắt.

**Khi nào KHÔNG dùng:** khi phương trình hoành độ giao điểm suy biến thành bậc
nhất (hệ số bậc hai bằng 0) — phải xét riêng.

**Bẫy thường gặp:**
- Nhầm "tiếp xúc" với "cắt tại một điểm" — cắt tại một điểm có thể do phương trình suy biến thành bậc nhất.
- Quên rằng đề hỏi "hai điểm phân biệt" cần Δ > 0 (không phải Δ ≥ 0).
- Tính Δ của phương trình chưa chuyển hết về một vế.

**Ví dụ:** Tìm m để (d): y = 2x + m tiếp xúc (P): y = x².
Phương trình hoành độ giao điểm: x² − 2x − m = 0. Tiếp xúc ⟺ Δ = 0 ⟺ 4 + 4m = 0 ⟺ m = −1.

## Hướng 4 — Điều kiện về tọa độ giao điểm (kết hợp Viète)

**Khi nào dùng:** đề cho điều kiện về x₁, x₂ của hai giao điểm.

**Khi nào KHÔNG dùng:** khi điều kiện liên quan tới y₁, y₂ — phải biểu diễn y
theo x trước rồi mới dùng Viète.

**Bẫy thường gặp:**
- Quên điều kiện Δ > 0 để có hai giao điểm phân biệt.
- Điều kiện về y nhưng áp Viète thẳng cho y (Viète chỉ đúng cho nghiệm x của phương trình hoành độ).
- Quên đối chiếu m tìm được với điều kiện có hai giao điểm.

---
### Ghi chú cho giáo viên
- Xem thêm sổ tay `find_parameter` cho phần Viète.

**Ví dụ:** Cho (P): y = x² và (d): y = mx + 1. Tìm m để (d) cắt (P) tại hai điểm có hoành độ x₁, x₂ thỏa x₁² + x₂² = 6.
Phương trình hoành độ: x² − mx − 1 = 0. Vì P = −1 < 0 nên luôn có hai nghiệm trái dấu.
Viète: S = m, P = −1. Ta có x₁² + x₂² = m² + 2 = 6 ⟺ m² = 4 ⟺ m = ±2.

