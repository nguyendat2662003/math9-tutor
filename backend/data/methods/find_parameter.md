---
goal_type: find_parameter
title_vi: Tìm tham số m thỏa điều kiện về nghiệm (ứng dụng Viète)
topics: [ALG-6]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Tìm giá trị tham số m thỏa điều kiện cho trước

> Dạng cực kỳ phổ biến — gần như đề vào 10 nào cũng có. Chìa khóa gần như luôn
> là định lý Viète (Bài 20).

## Quy trình chung (làm trước mọi hướng)

1. **Điều kiện có nghiệm:** tính Δ (hoặc Δ′), đặt Δ ≥ 0 (hoặc > 0 nếu cần hai
   nghiệm phân biệt). Bước học sinh HAY QUÊN nhất.
2. **Viết Viète:** x₁ + x₂ = −b/a ; x₁·x₂ = c/a.
3. **Biến đổi điều kiện đề bài** về dạng chứa tổng S và tích P.
4. **Giải tìm m**, rồi ĐỐI CHIẾU với điều kiện bước 1.

## Hướng 1 — Điều kiện đối xứng với hai nghiệm

**Khi nào dùng:** điều kiện đối xứng (đổi chỗ x₁, x₂ không đổi), ví dụ x₁² + x₂²,
x₁³ + x₂³, 1/x₁ + 1/x₂.

**Công thức chuyển đổi:**
- x₁² + x₂² = S² − 2P
- x₁³ + x₂³ = S³ − 3PS
- 1/x₁ + 1/x₂ = S/P (cần P ≠ 0)
- (x₁ − x₂)² = S² − 4P

**Khi nào KHÔNG dùng:** khi điều kiện KHÔNG đối xứng (ví dụ x₁ = 2x₂) — lúc đó
phải kết hợp thêm phương trình, dùng Hướng 2.

**Bẫy thường gặp:**
- Quên điều kiện Δ ≥ 0, dẫn tới nhận cả những m làm phương trình vô nghiệm.
- Quên điều kiện mẫu khác 0 khi biểu thức có phân thức (P ≠ 0, hoặc x₁, x₂ ≠ 0).
- Biến đổi sai công thức: hay nhầm x₁² + x₂² = S² − 2P thành S² + 2P.
- Tìm được m nhưng quên đối chiếu điều kiện, không loại nghiệm ngoại lai.


**Ví dụ:** Cho x² − 2(m+1)x + m² + 3 = 0. Tìm m để x₁² + x₂² = 20.
Δ′ = (m+1)² − (m²+3) = 2m − 2 ≥ 0 ⟺ m ≥ 1.
Viète: S = 2(m+1), P = m² + 3.
x₁² + x₂² = S² − 2P = 4(m+1)² − 2(m²+3) = 2m² + 8m − 2 = 20 ⟺ m² + 4m − 11 = 0 ⟺ m = −2 ± √15.
Đối chiếu m ≥ 1: chỉ nhận m = −2 + √15.

_Công cụ: T-VIETE_

## Hướng 2 — Điều kiện không đối xứng

> Nếu điều kiện chứa bình phương của một nghiệm (ví dụ x₁² + 2x₂ = 5), kỹ thuật
> **hạ bậc bằng cách thay nghiệm vào phương trình** thường nhanh hơn giải hệ ba
> phương trình. Xem sổ tay `evaluate_root_expression`, Hướng 2 — kỹ thuật này có mặt
> ở 4/5 đề phổ thông năm 2026.

**Khi nào dùng:** điều kiện dạng x₁ = 2x₂, x₁ − x₂ = 3, hoặc một nghiệm cho trước.

**Các bước:**
1. Viết Viète (2 phương trình).
2. Thêm phương trình từ điều kiện đề.
3. Giải hệ 3 phương trình tìm x₁, x₂, m.
4. Đối chiếu điều kiện có nghiệm.

**Khi nào KHÔNG dùng:** khi điều kiện đối xứng — dùng Hướng 1 gọn hơn nhiều.

**Bẫy thường gặp:**
- Giải hệ ra m nhưng quên kiểm tra Δ ≥ 0 với giá trị m đó.
- Với điều kiện x₁ = 2x₂, quên rằng vai trò x₁, x₂ có thể hoán đổi — cần xét cả hai trường hợp nếu đề không chỉ rõ.
- Thay nghiệm cho trước vào phương trình rồi quên tìm nghiệm còn lại khi đề hỏi.


**Ví dụ:** Cho x² − 5x + m = 0. Tìm m để x₁ = 4x₂.
Viète: x₁ + x₂ = 5 và x₁x₂ = m. Kết hợp x₁ = 4x₂ được 5x₂ = 5 nên x₂ = 1, x₁ = 4.
Suy ra m = 4·1 = 4. Kiểm tra Δ = 25 − 16 = 9 > 0, thỏa mãn. Vậy m = 4.

_Công cụ: T-VIETE_

## Hướng 3 — Điều kiện về dấu của nghiệm

**Khi nào dùng:** đề hỏi hai nghiệm cùng dấu, trái dấu, cùng dương, cùng âm.

**Bảng điều kiện:**
- Trái dấu: P < 0 (KHÔNG cần xét Δ, vì P < 0 đã kéo theo Δ > 0)
- Cùng dấu: Δ ≥ 0 và P > 0
- Cùng dương: Δ ≥ 0, P > 0, S > 0
- Cùng âm: Δ ≥ 0, P > 0, S < 0

**Khi nào KHÔNG dùng:** khi đề hỏi về độ lớn nghiệm (|x₁| > |x₂|) chứ không phải
dấu — cần cách tiếp cận khác.

**Bẫy thường gặp:**
- Xét thừa điều kiện Δ ở trường hợp trái dấu.
- Quên điều kiện a ≠ 0 khi hệ số a chứa tham số m.
- Nhầm "hai nghiệm dương" với "hai nghiệm không âm" (nghiệm bằng 0 có được nhận không).


**Ví dụ:** Cho x² − 2mx + m − 2 = 0. Tìm m để phương trình có hai nghiệm trái dấu.
Hai nghiệm trái dấu ⟺ P < 0 ⟺ m − 2 < 0 ⟺ m < 2. (Không cần xét Δ vì P < 0 đã kéo theo Δ > 0.)

_Công cụ: T-VIETE_

---
### Ghi chú cho giáo viên
- Dạng đại số quan trọng nhất — bổ sung nhiều bài minh họa cho cả ba hướng.
- Bảng dấu ở Hướng 3 nên được kiểm tra kỹ và bổ sung ví dụ.
