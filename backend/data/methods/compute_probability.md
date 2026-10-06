---
goal_type: compute_probability
title_vi: Tính xác suất của biến cố
topics: [PRO-8]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Xác suất của biến cố (Chương VIII — Bài 25, 26)

> ⚠ NỘI DUNG MỚI của GDPT 2018. Cần giáo viên soạn kỹ, ít tài liệu tham khảo cũ.

## Ba bước chuẩn cho mọi bài

1. **Mô tả phép thử và không gian mẫu Ω** — liệt kê tất cả kết quả có thể.
2. **Đếm số kết quả thuận lợi** cho biến cố A.
3. **Tính** P(A) = số kết quả thuận lợi / tổng số kết quả.

**Điều kiện quan trọng:** công thức trên chỉ đúng khi các kết quả ĐỒNG KHẢ NĂNG.

## Hướng 1 — Liệt kê trực tiếp không gian mẫu

**Khi nào dùng:** số kết quả ít (tung đồng xu, gieo xúc xắc, rút thẻ).

**Các bước:** liệt kê đầy đủ và có hệ thống, dùng bảng hoặc sơ đồ cây để không sót.

**Khi nào KHÔNG dùng:** khi số kết quả quá lớn (rút 3 thẻ từ 20 thẻ) — liệt kê
không khả thi, phải dùng lập luận đếm.

**Bẫy thường gặp:**
- Liệt kê sót hoặc trùng kết quả.
- Với hai xúc xắc: phải phân biệt (1;2) và (2;1) là hai kết quả khác nhau — không gian mẫu có 36 phần tử, không phải 21.
- Cho rằng các kết quả đồng khả năng khi thực ra không (ví dụ tổng hai xúc xắc: tổng 7 nhiều khả năng hơn tổng 2).

**Ví dụ:** Gieo một con xúc xắc cân đối. Không gian mẫu Ω = {1; 2; 3; 4; 5; 6}, có 6 kết quả đồng khả năng. Biến cố A: "số chấm là số chẵn" có 3 kết quả thuận lợi {2; 4; 6}. Vậy P(A) = 3/6 = 1/2.

## Hướng 2 — Dùng sơ đồ cây

**Khi nào dùng:** phép thử gồm nhiều giai đoạn (tung đồng xu 2–3 lần, rút liên tiếp).

**Khi nào KHÔNG dùng:** khi số giai đoạn nhiều (từ 4 trở lên) — cây quá lớn, khó
vẽ và dễ sót nhánh.

**Bẫy thường gặp:**
- Không phân biệt rút CÓ hoàn lại và KHÔNG hoàn lại — số kết quả ở nhánh sau khác nhau.
- Vẽ thiếu nhánh ở tầng cuối.
- Đếm nhánh mà quên rằng các nhánh phải đồng khả năng.

**Ví dụ:** Tung một đồng xu hai lần. Sơ đồ cây cho 4 kết quả: SS, SN, NS, NN (S: sấp, N: ngửa). Biến cố B: "có đúng một lần sấp" gồm SN và NS, tức 2 kết quả. Vậy P(B) = 2/4 = 1/2.

## Hướng 3 — Dùng bảng hai chiều

**Khi nào dùng:** phép thử gồm hai hành động độc lập (gieo hai xúc xắc, rút một
thẻ từ mỗi hộp).

**Khi nào KHÔNG dùng:** khi có từ ba hành động trở lên — bảng hai chiều không
biểu diễn được, phải dùng sơ đồ cây.

**Bẫy thường gặp:**
- Đánh dấu ô thuận lợi sót hoặc thừa.
- Nhầm số ô của bảng với số kết quả thuận lợi.
- Với hai hành động không độc lập (rút không hoàn lại), bảng có ô không hợp lệ cần loại.

**Ví dụ:** Gieo hai con xúc xắc. Lập bảng 6×6 được 36 kết quả. Biến cố C: "tổng số chấm bằng 7" gồm (1;6), (2;5), (3;4), (4;3), (5;2), (6;1) — 6 kết quả. Vậy P(C) = 6/36 = 1/6.

## Hướng 4 — Biến cố đối

**Khi nào dùng:** đếm trực tiếp khó nhưng đếm biến cố đối dễ. P(A) = 1 − P(Ā).

**Dấu hiệu nhận biết:** đề có "ít nhất một", "không phải tất cả".

**Khi nào KHÔNG dùng:** khi biến cố đối cũng khó đếm không kém — lúc đó đếm trực
tiếp cho rõ ràng hơn.

**Bẫy thường gặp:**
- Xác định sai biến cố đối. Đối của "ít nhất một" là "không có cái nào", KHÔNG phải "nhiều nhất một".
- Đối của "cả hai đều đỏ" là "có ít nhất một không đỏ", không phải "cả hai đều không đỏ".
- Tính P(Ā) rồi quên lấy 1 trừ đi.

**Ví dụ:** Tung đồng xu 3 lần. Tính xác suất có ÍT NHẤT một lần sấp.
Biến cố đối là "không có lần nào sấp", tức cả 3 lần đều ngửa — chỉ 1 kết quả trong 8. P(đối) = 1/8.
Vậy xác suất cần tìm = 1 − 1/8 = 7/8.

## Ghi nhớ kiểm tra kết quả

- 0 ≤ P(A) ≤ 1 luôn đúng. Kết quả ngoài khoảng này là sai.
- P = 0: biến cố không thể. P = 1: biến cố chắc chắn.
- Nên tự hỏi "con số này có hợp lý không" trước khi kết luận.

**Bẫy chung:** viết xác suất lớn hơn 1 do đếm số thuận lợi lớn hơn tổng số kết quả.

---
### Ghi chú cho giáo viên — ƯU TIÊN CAO
- Cần xác nhận KNTT lớp 9 dạy tới đâu: có xác suất của biến cố hợp/giao không,
  hay chỉ dừng ở mô hình đơn giản?
- Bổ sung bài minh họa từ SGK KNTT và đề thi 2024–2025.
