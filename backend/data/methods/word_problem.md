---
goal_type: word_problem
title_vi: Giải bài toán bằng cách lập phương trình, hệ phương trình
topics: [ALG-1, ALG-6]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Giải bài toán bằng cách lập phương trình / hệ phương trình

> Bài 3 (lập hệ) và Bài 21 (lập phương trình). Điểm mất nhiều nhất không phải ở
> giải phương trình mà ở bước LẬP và ĐẶT điều kiện cho ẩn.

## Quy trình bốn bước (bắt buộc theo thứ tự)

1. **Gọi ẩn và đặt điều kiện** (dương, nguyên, nhỏ hơn tổng...).
2. **Biểu diễn các đại lượng** khác theo ẩn.
3. **Lập phương trình** từ mối quan hệ đề cho.
4. **Giải và đối chiếu điều kiện**, trả lời có đơn vị.

## Hướng 1 — Toán chuyển động

**Dấu hiệu nhận biết:** đề nhắc vận tốc, quãng đường, thời gian; hai vật hoặc hai chặng.

**Mẹo lập:** dùng s = v·t. Lập bảng ba cột (s, v, t) cho từng chặng rồi lập
phương trình từ cột thời gian hoặc quãng đường.

**Khi nào KHÔNG dùng một ẩn:** khi có hai đại lượng chưa biết độc lập (ví dụ cả
vận tốc và thời gian đều chưa biết, không suy được từ nhau) — dùng hệ hai ẩn.

**Bẫy thường gặp:**
- Đơn vị không nhất quán (km/h với phút) — phải đổi trước khi lập phương trình.
- Quên thời gian nghỉ, thời gian chờ khi tính tổng thời gian.
- Bài xuôi dòng / ngược dòng: vận tốc xuôi = v thuyền + v dòng, ngược = v thuyền − v dòng. Hay bị đảo dấu.
- Quên điều kiện vận tốc dòng nước nhỏ hơn vận tốc thuyền.

**Ví dụ:** Một ô tô đi từ A đến B dài 120 km. Lúc về vận tốc tăng 10 km/h nên thời gian về ít hơn 36 phút. Tính vận tốc lúc đi.
Gọi vận tốc lúc đi là x (km/h), x > 0. Thời gian đi 120/x, thời gian về 120/(x+10). Đổi 36 phút = 3/5 giờ.
Phương trình: 120/x − 120/(x+10) = 3/5. Giải ra x = 40 (loại nghiệm âm). Vậy vận tốc lúc đi là 40 km/h.

## Hướng 2 — Toán năng suất, công việc chung

**Dấu hiệu nhận biết:** "làm chung", "làm riêng", "vòi nước", "đội thợ".

**Mẹo lập:** quy về công việc làm trong 1 đơn vị thời gian: 1/x + 1/y = 1/t.

**Khi nào KHÔNG dùng:** khi đề cho năng suất trực tiếp (số sản phẩm/giờ) thay vì
thời gian hoàn thành — lúc đó lập phương trình theo số sản phẩm đơn giản hơn.

**Bẫy thường gặp:**
- Cộng thời gian thay vì cộng năng suất. Hai người làm chung KHÔNG phải cộng thời gian.
- Quên điều kiện x > 0, y > 0.
- Bài "làm được một phần rồi người kia làm tiếp" — phải chia giai đoạn, dễ lập sai.

**Ví dụ:** Hai đội làm chung một công việc trong 6 giờ thì xong. Nếu làm riêng, đội I cần ít hơn đội II là 5 giờ. Tính thời gian mỗi đội làm riêng.
Gọi thời gian đội I làm riêng là x (giờ), x > 0; đội II là x + 5.
Phương trình: 1/x + 1/(x+5) = 1/6. Giải ra x = 10 (loại nghiệm âm). Vậy đội I cần 10 giờ, đội II cần 15 giờ.

## Hướng 3 — Toán số học, hình học, phần trăm

**Dấu hiệu nhận biết:** tìm số có hai chữ số, bài toán về tuổi, tăng giảm phần trăm.

**Khi nào KHÔNG dùng:** khi bài thực chất là chuyển động hoặc năng suất được
diễn đạt khác đi — đọc kỹ để phân loại đúng.

**Bẫy thường gặp:**
- Số có hai chữ số: viết là 10a + b, KHÔNG phải a·b. Điều kiện: a từ 1–9, b từ 0–9, đều nguyên.
- Bài phần trăm: nhầm "tăng 20%" (nhân 1,2) với "tăng lên 20%" (nhân 0,2).
- Bài tuổi: quên rằng hiệu số tuổi không đổi theo thời gian.
- Kết quả ra số thập phân trong khi đề đòi số nguyên (số người, số sản phẩm) — phải loại.

**Ví dụ:** Tìm số có hai chữ số, biết tổng hai chữ số bằng 9 và nếu đổi chỗ hai chữ số thì được số mới lớn hơn số ban đầu 27 đơn vị.
Gọi chữ số hàng chục là a, hàng đơn vị là b; a từ 1–9, b từ 0–9, nguyên. Số ban đầu 10a + b.
Hệ: a + b = 9 và (10b + a) − (10a + b) = 27, tức b − a = 3.
Giải hệ: a = 3, b = 6. Vậy số cần tìm là 36.

## Chọn một ẩn hay hai ẩn

**Dùng hệ hai ẩn khi:** có hai đại lượng chưa biết độc lập và hai mối quan hệ rõ ràng.

**KHÔNG dùng hai ẩn khi:** biểu diễn được đại lượng thứ hai theo đại lượng thứ
nhất — lúc đó một ẩn gọn hơn, ít sai sót hơn.

---
### Ghi chú cho giáo viên
- Bổ sung 1 bài minh họa hoàn chỉnh cho mỗi loại.
- Nhấn mạnh bước đặt điều kiện và đối chiếu — nơi mất điểm nhiều nhất.
