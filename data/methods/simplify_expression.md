---
goal_type: simplify_expression
title_vi: Rút gọn biểu thức chứa căn thức và các câu hỏi phụ
topics: [ALG-3]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Rút gọn biểu thức chứa căn và các ý phụ

> Thường là câu 1 đề vào 10 (câu "gỡ điểm"). Gồm ý rút gọn và các ý phụ.

## Bước 0 — Điều kiện xác định (LÀM ĐẦU TIÊN, luôn luôn)

Biểu thức dưới căn ≥ 0, mẫu ≠ 0. Bước học sinh hay bỏ qua và bị trừ điểm.

## Hướng 1 — Quy đồng và rút gọn

**Khi nào dùng:** biểu thức là tổng/hiệu các phân thức chứa căn.

**Các bước:**
1. Đặt điều kiện xác định.
2. Phân tích các mẫu thành nhân tử (thường a − b = (√a − √b)(√a + √b)).
3. Quy đồng, cộng trừ tử.
4. Rút gọn, kết luận KÈM điều kiện.

**Khi nào KHÔNG dùng:** khi biểu thức không có mẫu chứa căn mà chỉ cần đưa thừa
số ra ngoài dấu căn — lúc đó biến đổi trực tiếp nhanh hơn.

**Bẫy thường gặp:**
- Nhớ nhầm √(A²) = A. Đúng phải là √(A²) = |A|, chỉ bằng A khi A ≥ 0.
- Quên trục căn thức ở mẫu khi đề yêu cầu.
- Rút gọn xong quên ghi lại điều kiện xác định.
- Chia cả tử và mẫu cho biểu thức có thể bằng 0.


**Ví dụ:** Rút gọn A = (√x)/(√x − 2) + 4/(√x + 2) với x ≥ 0, x ≠ 4.
Mẫu chung (√x − 2)(√x + 2) = x − 4.
A = [√x(√x + 2) + 4(√x − 2)] / (x − 4) = (x + 2√x + 4√x − 8)/(x − 4) = (x + 6√x − 8)/(x − 4).

_Công cụ: T-RADICAL-OPERATIONS_

## Hướng 2 (ý phụ) — Tính giá trị biểu thức tại x cho trước

**Khi nào dùng:** sau khi rút gọn, đề cho x = giá trị cụ thể (thường chứa căn).

**Các bước:**
1. Kiểm tra x có thỏa điều kiện xác định không.
2. Nếu x chứa căn, biến đổi về dạng đẹp trước khi thay (ví dụ đưa về bình phương đủ).
3. Thay vào biểu thức ĐÃ RÚT GỌN.

**Khi nào KHÔNG dùng:** khi x không thỏa điều kiện xác định — phải kết luận
biểu thức không xác định tại giá trị đó.

**Bẫy thường gặp:**
- Thay vào biểu thức GỐC thay vì biểu thức đã rút gọn, làm tính toán rối.
- Quên kiểm tra điều kiện xác định của giá trị x được cho.
- Không rút gọn được x dạng √(a ± 2√b) về dạng (√m ± √n) nên tính sai.

**Ví dụ:** Với A đã rút gọn ở trên, tính A tại x = 9. Kiểm tra x = 9 thỏa điều kiện (x ≥ 0, x ≠ 4). Thay vào: A = (9 + 6·3 − 8)/(9 − 4) = 19/5.

## Hướng 3 (ý phụ) — Tìm x để biểu thức thỏa điều kiện

**Khi nào dùng:** đề hỏi tìm x để A > 0, A = k, hoặc A nhận giá trị nguyên.

**Các bước:**
1. Dùng biểu thức đã rút gọn.
2. Với A nguyên: tách thành phần nguyên + phân số, cho mẫu là ước của tử.
3. Đối chiếu điều kiện xác định, loại nghiệm không thỏa.

**Khi nào KHÔNG dùng:** khi biểu thức chưa rút gọn được — phải làm ý rút gọn trước.

**Bẫy thường gặp:**
- Quên đối chiếu điều kiện xác định ở cuối — lỗi mất điểm phổ biến nhất.
- Với bài tìm x nguyên: quên loại giá trị làm mẫu bằng 0, hoặc quên điều kiện x ≥ 0.
- Giải bất phương trình A > 0 mà quên xét dấu mẫu.
- Tìm được x nhưng quên kiểm tra x có phải số nguyên/tự nhiên như đề yêu cầu không.


**Ví dụ:** Tìm x nguyên để B = (√x + 3)/(√x + 1) nhận giá trị nguyên (x ≥ 0).
B = 1 + 2/(√x + 1). Để B nguyên thì (√x + 1) là ước dương của 2, tức √x + 1 ∈ {1; 2}, suy ra √x ∈ {0; 1}, tức x ∈ {0; 1}. Cả hai đều thỏa x ≥ 0.

_Công cụ: T-RADICAL-OPERATIONS_

---
### Ghi chú cho giáo viên
- Nhấn mạnh Bước 0 — lỗi mất điểm phổ biến nhất toàn bài.
