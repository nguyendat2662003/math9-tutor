---
goal_type: solve_equation
title_vi: Giải phương trình
topics: [ALG-2, ALG-3, ALG-6]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Giải phương trình

## Hướng 1 — Phương trình bậc hai một ẩn (Bài 19)

**Các bước:** đưa về ax² + bx + c = 0 → tính Δ = b² − 4ac (hoặc Δ′ = b′² − ac khi
b chẵn) → kết luận theo dấu Δ, tính nghiệm.

**Mẹo nhẩm nghiệm:** nếu a + b + c = 0 thì x₁ = 1, x₂ = c/a. Nếu a − b + c = 0
thì x₁ = −1, x₂ = −c/a. Dùng được sẽ tiết kiệm nhiều thời gian trong phòng thi.

**Khi nào KHÔNG dùng:** khi hệ số a chứa tham số và có thể bằng 0 — phải xét
riêng trường hợp a = 0 (khi đó là phương trình bậc nhất).

**Bẫy thường gặp:**
- Quên xét a = 0 khi hệ số chứa tham số.
- Nhầm dấu khi tính Δ, đặc biệt khi c âm (−4ac thành cộng).
- Dùng Δ′ nhưng quên rằng b′ = b/2, và công thức nghiệm cũng khác.
- Δ = 0 kết luận "vô nghiệm" thay vì "nghiệm kép".


**Ví dụ:** Giải x² − 5x + 6 = 0. Vì 1 + (−5) + 6 = 2 ≠ 0 nên không nhẩm được theo mẹo; tính Δ = 25 − 24 = 1 > 0, √Δ = 1. Nghiệm x₁ = (5+1)/2 = 3; x₂ = (5−1)/2 = 2.

_Công cụ: T-QUADRATIC-FORMULA, T-DELTA-PRIME_

## Hướng 2 — Phương trình tích (Bài 4)

**Khi nào dùng:** đưa được về dạng A·B = 0.

**Khi nào KHÔNG dùng:** khi không phân tích được thành nhân tử — thử đặt ẩn phụ
hoặc dùng công thức nghiệm.

**Bẫy thường gặp:**
- Chia cả hai vế cho một biểu thức chứa ẩn (làm mất nghiệm). Phải chuyển vế và đặt nhân tử chung.
- Chỉ giải một nhân tử, quên nhân tử còn lại.
- Kết luận thiếu nghiệm khi một nhân tử là phương trình bậc hai.

**Ví dụ:** Giải (x − 1)(x² − 4) = 0. Phương trình tích: x − 1 = 0 hoặc x² − 4 = 0, suy ra x = 1; x = 2; x = −2.

## Hướng 3 — Phương trình chứa ẩn ở mẫu (Bài 4)

**Các bước:**
1. Đặt ĐIỀU KIỆN XÁC ĐỊNH (mẫu ≠ 0) — bắt buộc.
2. Quy đồng, khử mẫu.
3. Giải phương trình thu được.
4. ĐỐI CHIẾU điều kiện, loại nghiệm không thỏa.

**Khi nào KHÔNG dùng:** khi phương trình có thể rút gọn trực tiếp mà không cần
quy đồng (ví dụ hai vế cùng mẫu).

**Bẫy thường gặp:**
- Quên đối chiếu điều kiện — lỗi mất điểm phổ biến nhất của dạng này.
- Đặt điều kiện sau khi đã khử mẫu (phải đặt TRƯỚC).
- Quy đồng sai, đặc biệt khi mẫu cần phân tích thành nhân tử trước.

**Ví dụ:** Giải 1/(x−1) + 2/(x+1) = 1. Điều kiện x ≠ ±1. Quy đồng: (x+1) + 2(x−1) = x² − 1 ⟺ 3x − 1 = x² − 1 ⟺ x² − 3x = 0 ⟺ x = 0 hoặc x = 3. Cả hai thỏa điều kiện.

## Hướng 4 — Phương trình chứa căn

**Các bước:**
1. Đặt điều kiện (biểu thức dưới căn ≥ 0, và vế còn lại ≥ 0 nếu bình phương).
2. Bình phương hai vế hoặc đặt ẩn phụ.
3. THỬ LẠI nghiệm.

**Khi nào KHÔNG dùng bình phương trực tiếp:** khi vế còn lại có thể âm — phải
đặt thêm điều kiện, nếu không sẽ sinh nghiệm ngoại lai.

**Bẫy thường gặp:**
- Bình phương hai vế sinh nghiệm ngoại lai — BẮT BUỘC thử lại.
- Quên điều kiện vế phải ≥ 0 trước khi bình phương.
- Bình phương sai với biểu thức có hai căn (phải chuyển vế để còn một căn mỗi lần).

**Ví dụ:** Giải √(x + 3) = x − 3. Điều kiện x ≥ −3 và x − 3 ≥ 0, tức x ≥ 3. Bình phương: x + 3 = x² − 6x + 9 ⟺ x² − 7x + 6 = 0 ⟺ x = 1 hoặc x = 6. Đối chiếu x ≥ 3: chỉ nhận x = 6.

## Hướng 5 — Đặt ẩn phụ

**Khi nào dùng:** phương trình có biểu thức lặp lại, hoặc dạng trùng phương
ax⁴ + bx² + c = 0 (đặt t = x², t ≥ 0).

**Khi nào KHÔNG dùng:** khi biểu thức lặp không thực sự giống nhau hoàn toàn —
đặt ẩn phụ sẽ làm phương trình phức tạp hơn.

**Bẫy thường gặp:**
- Quên điều kiện của ẩn phụ (t = x² thì t ≥ 0) — nhận cả nghiệm t âm.
- Giải ra t rồi quên quay lại tìm x.
- Với t = x² và t > 0, quên rằng x có HAI giá trị ±√t.

**Ví dụ:** Giải x⁴ − 5x² + 4 = 0. Đặt t = x², t ≥ 0: t² − 5t + 4 = 0 ⟺ t = 1 hoặc t = 4 (cả hai đều ≥ 0). Với t = 1: x = ±1. Với t = 4: x = ±2. Vậy phương trình có 4 nghiệm.

