---
goal_type: solve_system
title_vi: Giải hệ hai phương trình bậc nhất hai ẩn
topics: [ALG-1]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Giải hệ hai phương trình bậc nhất hai ẩn (Chương I — Bài 2)

## Hướng 1 — Phương pháp thế

**Khi nào dùng:** một phương trình có hệ số của một ẩn bằng 1 hoặc −1 — rút ẩn
đó ra dễ dàng.

**Các bước:** rút một ẩn theo ẩn kia → thế vào phương trình còn lại → giải →
thay ngược tìm ẩn thứ hai.

**Khi nào KHÔNG dùng:** khi mọi hệ số đều khác 1 và −1 — rút ra sẽ có phân số,
dễ sai. Lúc đó dùng cộng đại số.

**Bẫy thường gặp:**
- Sai dấu khi rút và thế, đặc biệt khi hệ số âm.
- Thế vào chính phương trình vừa rút ra (được 0 = 0, không giải được).
- Tìm được một ẩn rồi quên thay ngược tìm ẩn còn lại.
- Quên kết luận nghiệm dưới dạng cặp (x; y).

**Ví dụ:** Giải hệ: x + 2y = 5 và 3x − y = 1. Từ phương trình đầu rút x = 5 − 2y. Thế vào: 3(5 − 2y) − y = 1 ⟺ 15 − 7y = 1 ⟺ y = 2. Suy ra x = 1. Nghiệm (x; y) = (1; 2).

## Hướng 2 — Phương pháp cộng đại số

**Khi nào dùng:** hệ số của một ẩn ở hai phương trình bằng nhau hoặc đối nhau,
hoặc dễ nhân để làm bằng.

**Các bước:** nhân hai vế để hệ số một ẩn bằng/đối nhau → cộng (hoặc trừ) hai
phương trình để khử ẩn → giải và thay ngược.

**Khi nào KHÔNG dùng:** khi hệ có dạng đặc biệt dễ rút một ẩn — phương pháp thế
nhanh hơn.

**Bẫy thường gặp:**
- Nhân thiếu một vế (chỉ nhân vế trái mà quên vế phải).
- Sai dấu khi TRỪ hai phương trình — nên chuyển thành phép cộng với số đối.
- Nhân với số 0 (khi hệ số chứa tham số).

**Ví dụ:** Giải hệ: 2x + 3y = 7 và 2x − y = 3. Trừ vế theo vế: 4y = 4 nên y = 1. Thay vào phương trình thứ hai: 2x = 4 nên x = 2. Nghiệm (2; 1).

## Hướng 3 — Đặt ẩn phụ

**Khi nào dùng:** hệ chứa biểu thức lặp như 1/x, 1/y, hoặc căn thức.

**Các bước:** đặt ẩn phụ KÈM ĐIỀU KIỆN → giải hệ mới → trả về ẩn ban đầu → đối
chiếu điều kiện.

**Khi nào KHÔNG dùng:** khi các biểu thức không thực sự lặp lại giống nhau.

**Bẫy thường gặp:**
- Quên điều kiện của ẩn phụ và của ẩn gốc (x ≠ 0 khi đặt u = 1/x).
- Giải ra ẩn phụ rồi quên quay về ẩn gốc.
- Đối chiếu điều kiện với ẩn phụ mà quên đối chiếu với ẩn gốc.

**Ví dụ:** Giải hệ: 1/x + 1/y = 5/6 và 1/x − 1/y = 1/6 (x, y ≠ 0). Đặt u = 1/x, v = 1/y. Hệ thành u + v = 5/6 và u − v = 1/6, giải ra u = 1/2, v = 1/3. Suy ra x = 2, y = 3 (thỏa điều kiện).

## Hướng 4 — Biện luận số nghiệm theo tham số

**Khi nào dùng:** đề hỏi tìm m để hệ có nghiệm duy nhất / vô nghiệm / vô số nghiệm.

**Mẹo:** so sánh tỉ số a/a′, b/b′, c/c′.
- a/a′ ≠ b/b′ : nghiệm duy nhất
- a/a′ = b/b′ ≠ c/c′ : vô nghiệm
- a/a′ = b/b′ = c/c′ : vô số nghiệm

**Khi nào KHÔNG dùng:** khi một trong các hệ số a′, b′, c′ bằng 0 — không lập
được tỉ số. Phải xét riêng trường hợp đó trước.

**Bẫy thường gặp:**
- Lập tỉ số khi mẫu bằng 0.
- Quên xét riêng trường hợp hệ số của cả hai ẩn cùng bằng 0.
- Nhầm điều kiện vô nghiệm với vô số nghiệm (khác nhau ở tỉ số c/c′).

**Ví dụ:** Tìm m để hệ mx + y = 3 và 2x + y = 1 có nghiệm duy nhất. Điều kiện: m/2 ≠ 1/1, tức m ≠ 2. Vậy hệ có nghiệm duy nhất khi m ≠ 2.

