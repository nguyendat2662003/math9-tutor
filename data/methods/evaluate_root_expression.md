---
goal_type: evaluate_root_expression
title_vi: Tính giá trị biểu thức chứa nghiệm (không giải phương trình)
topics: [ALG-6]
modes: [basic, exam10]
status: needs_teacher
provenance: Rút từ đề tuyển sinh 10 năm 2026 (Hà Nội, Quảng Ninh, Thanh Hóa, Hưng Yên) — cần giáo viên xác nhận
---
# Tính giá trị biểu thức chứa nghiệm

> Sổ tay này được bổ sung sau khi phân tích đề thi thật. Qua 8 đề phổ thông năm
> 2026: **cả 8 đề** có câu tính biểu thức nghiệm bằng Viète, trong đó **6 đề** là
> biểu thức KHÔNG đối xứng — phải hạ bậc hoặc đối xứng hóa trước. Bộ sổ tay ban
> đầu chưa có các kỹ thuật này.
>
> Khác với `find_parameter`: ở đây yêu cầu chính là TÍNH một giá trị (tham số nếu
> có thì đã biết hoặc chỉ cần giải sau cùng).

## Hướng 1 — Biểu thức đối xứng: đưa về tổng S và tích P

**Khi nào dùng:** đổi chỗ x₁ và x₂ thì biểu thức không đổi.

**Công thức hay dùng:** x₁² + x₂² = S² − 2P; x₁³ + x₂³ = S³ − 3PS;
1/x₁ + 1/x₂ = S/P; (x₁ − x₂)² = S² − 4P.

**Khi nào KHÔNG dùng:** khi biểu thức không đối xứng — dấu hiệu là x₁ và x₂ xuất
hiện với vai trò khác nhau, ví dụ x₁² + 2x₂. Lúc đó dùng Hướng 2.

**Bẫy thường gặp:**
- Quên kiểm tra phương trình có nghiệm (Δ ≥ 0) trước khi dùng Viète.
- Nhớ nhầm x₁² + x₂² = S² + 2P.
- Chia cho P khi P có thể bằng 0.

**Ví dụ:** x² − 3x + 1 = 0 có S = 3, P = 1 nên x₁² + x₂² = 9 − 2 = 7.

## Hướng 2 — Hạ bậc bằng cách thay nghiệm vào chính phương trình

**Khi nào dùng:** biểu thức KHÔNG đối xứng và có bình phương của một nghiệm.

**Ý tưởng:** x₁ là nghiệm của ax² + bx + c = 0 nên a·x₁² = −b·x₁ − c. Thay vào để
hạ bậc; phần còn lại thường ghép được thành S hoặc P.

**Các bước:**
1. Viết Viète: S = x₁ + x₂, P = x₁x₂.
2. Từ phương trình, rút x₁² (hoặc x₂²) theo x₁ (hoặc x₂).
3. Thay vào biểu thức, thu gọn. Tách hệ số khéo để xuất hiện x₁ + x₂.
4. Nếu có tham số: giải ra rồi ĐỐI CHIẾU điều kiện Δ.

**Khi nào KHÔNG dùng:** khi biểu thức đối xứng — Hướng 1 nhanh hơn.

**Bẫy thường gặp:**
- Thay sai hệ thức: x₁² = 3x₁ − 1 chỉ đúng vì x₁ là nghiệm của CHÍNH phương trình đó.
- Sau khi hạ bậc còn sót một số hạng x₁ hoặc x₂ lẻ, không ghép được thành S — phải tách hệ số lại (ví dụ −4x₂ = −3x₂ − x₂).
- Biểu thức không đối xứng có thể cho hai giá trị tùy cách gán x₁, x₂. Nếu đề không cho thứ tự thì phải kiểm tra cả hai.
- Có tham số mà quên đối chiếu Δ > 0.

**Ví dụ 1 (Hà Nội 2026):** x² − 3x + 1 = 0, tính Q = (3x₂ − 1)/x₁ + 3x₁/x₂ − x₁.
Ghép Q = 3(x₂/x₁ + x₁/x₂) − (1 + x₁²)/x₁. Vì x₁² + 1 = 3x₁ nên (1 + x₁²)/x₁ = 3.
Lại có x₂/x₁ + x₁/x₂ = (x₁² + x₂²)/(x₁x₂) = 7/1 = 7. Vậy Q = 21 − 3 = 18.

**Ví dụ 2 (Thanh Hóa 2026):** x² − 3x + m − 3 = 0, tìm m để x₂² + 4x₂(x₁ − 1) − x₁ = m − 2.
Vì x₂ là nghiệm nên x₂² − 3x₂ = 3 − m. Tách vế trái:
(x₂² − 3x₂) + 4x₁x₂ − (x₁ + x₂) = (3 − m) + 4(m − 3) − 3 = 3m − 12.
Giải 3m − 12 = m − 2 được m = 5. Đối chiếu Δ = 21 − 4m > 0 ⟺ m < 21/4: thỏa mãn.

**Ví dụ 3 (Hưng Yên 2026):** x² − 2x + 3m + 1 = 0, x₁² + 2x₂ = 5.
x₁² = 2x₁ − 3m − 1 nên x₁² + 2x₂ = 2(x₁ + x₂) − 3m − 1 = 3 − 3m = 5, suy ra m = −2/3.
Đối chiếu Δ′ = −3m > 0 ⟺ m < 0: thỏa mãn.

_Công cụ: T-VIETE_

## Hướng 3 — Biểu thức có căn: đưa biểu thức dưới căn về bình phương

**Khi nào dùng:** biểu thức chứa √(…) của các nghiệm; thường đề cho sẵn thứ tự
x₁ > x₂ — đó là gợi ý để bỏ dấu giá trị tuyệt đối.

**Các bước:**
1. Dùng S để thay một nghiệm theo nghiệm kia (x₂ = S − x₁).
2. Biến đổi biểu thức dưới căn thành bình phương đủ.
3. √(A²) = |A|; dùng thứ tự nghiệm để xác định dấu của A.
4. Hạ bậc phần còn lại theo Hướng 2.

**Khi nào KHÔNG dùng:** khi biểu thức dưới căn không đưa được về bình phương —
khi đó thường phải tính nghiệm cụ thể (nhưng đề "không giải phương trình" thì
hầu như luôn đưa được).

**Bẫy thường gặp:**
- Bỏ trị tuyệt đối mà không chứng minh dấu — mất điểm dù kết quả đúng.
- Không dùng điều kiện x₁ > x₂ đề cho sẵn.

**Ví dụ (Quảng Ninh 2026):** x² − 4x + 1 = 0, x₁ > x₂, tính P = (x₂ + 3)√(x₁² + 2x₂ − 7) − x₁².
Vì x₂ = 4 − x₁ nên x₁² + 2x₂ − 7 = (x₁ − 1)². Từ 2x₁ > x₁ + x₂ = 4 có x₁ > 2, nên
√(…) = x₁ − 1. Thay x₁² = 4x₁ − 1:
P = (x₁ − 1)(x₂ + 3) − 4x₁ + 1 = x₁x₂ − (x₁ + x₂) − 2 = 1 − 4 − 2 = −5.

**Ví dụ 2 (Nghệ An 2026) — cộng thêm bội của phương trình để tạo bình phương đủ:**
x² − 5x + 1 = 0, tính P = 1/(2 + √(23x₁² − 1)) + (3x₂² + 7)/(5x₂ + 1).
Biểu thức 23x₁² − 1 chưa phải bình phương. Cộng thêm 2(x₁² − 5x₁ + 1) — bằng 0 vì
x₁ là nghiệm — được 25x₁² − 10x₁ + 1 = (5x₁ − 1)². Vậy √(…) = 5x₁ − 1 = x₁² (dương).
Tương tự 5x₂ + 1 = x₂² + 2. Khi đó P = 3 + 1/(x₁² + 2) + 1/(x₂² + 2) — đã đối
xứng, đưa về S, P được P = 60/17.

**Mẹo tìm hệ số cần cộng:** muốn a·x² + c + k(x² − 5x + 1) là bình phương đủ thì
biệt thức của nó bằng 0 — giải ra k.

_Công cụ: T-VIETE_

## Hướng 4 — Đối xứng hóa bằng cách thay hằng số bằng S

**Khi nào dùng:** biểu thức gần đối xứng, chỉ lệch bởi một số hạng bậc thấp hơn có
hằng số trùng với tổng S (hoặc tích P).

**Ý tưởng:** nếu x₁ + x₂ = 2 thì 2x₁ = (x₁ + x₂)x₁ = x₁² + x₁x₂. Thay hằng số bằng S
để mọi số hạng cùng bậc, biểu thức trở thành đối xứng.

**Khi nào KHÔNG dùng:** khi hằng số không liên quan tới S hoặc P — dùng Hướng 2.

**Bẫy thường gặp:**
- Thay nhầm hằng số bằng S khi hằng số chỉ tình cờ bằng giá trị S với một tham số cụ thể.
- Đối xứng hóa xong quên đối chiếu điều kiện Δ.

**Ví dụ (Bắc Ninh 2026):** x² − 2x + m − 1 = 0, tìm m để x₁² + 2x₂² + 2x₁ + m² = 9.
Vì x₁ + x₂ = 2 nên 2x₁ = x₁² + x₁x₂. Vế trái thành 2(x₁² + x₂²) + x₁x₂ + m²
= 2(S² − 2P) + P + m² = 11 − 3m + m². Giải m² − 3m + 2 = 0 được m = 1 hoặc m = 2;
đối chiếu Δ′ = 2 − m > 0 chỉ nhận m = 1.
Cách khác: hạ bậc theo Hướng 2 cũng ra 11 − 3m — hai cách kiểm tra chéo cho nhau.

_Công cụ: T-VIETE_

---
### Ghi chú cho giáo viên
- Các ví dụ lấy từ đề thi thật và đã được kiểm chứng bằng SymPy (giải lại độc lập).
- Nên kiểm tra cách trình bày khớp hướng dẫn chấm: HDC Quảng Ninh chấm 0,25 điểm
  riêng cho bước chứng minh x₁ − 1 > 0.
