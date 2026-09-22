---
goal_type: prove_concurrent
title_vi: Chứng minh ba đường thẳng đồng quy
topics: [GEO-5, GEO-9]
modes: [exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Chứng minh ba đường thẳng đồng quy

> Ở lớp 9 KHÔNG được dùng định lý Ceva. Cách chuẩn là quy về chứng minh đường
> thứ ba đi qua giao điểm của hai đường đầu.

## Hướng 1 — Gọi giao điểm rồi chứng minh đường thứ ba đi qua

**Khi nào dùng:** hướng chuẩn, dùng được cho hầu hết bài.

**Các bước:**
1. Gọi I là giao điểm của hai đường thứ nhất và thứ hai.
2. Chứng minh I nằm trên đường thứ ba (thường bằng cách chứng minh ba điểm thẳng hàng).

**Khi nào KHÔNG dùng:** khi hai đường đầu tiên song song (không có giao điểm).
Phải chọn cặp đường khác, hoặc chứng minh chúng cắt nhau trước.

**Bẫy thường gặp:**
- Gọi giao điểm I mà không khẳng định hai đường CÓ cắt nhau — phải nêu lý do.
- Chứng minh I thuộc đường thứ ba nhưng dùng chính giả thiết đồng quy — lập luận vòng.
- Chọn cặp đường khó nhất để lấy giao điểm; nên chọn hai đường có giao điểm dễ mô tả nhất.

**Ví dụ:** Cho ΔABC, các đường cao BE và CF cắt nhau tại H. Chứng minh AH, BE, CF đồng quy: gọi H là giao của BE và CF (hai đường cao không song song nên cắt nhau), rồi chứng minh AH ⊥ BC, tức AH cũng là đường cao. Vậy ba đường đồng quy tại H.

## Hướng 2 — Dùng các điểm đặc biệt của tam giác

**Khi nào dùng:** ba đường là ba đường cao, ba trung tuyến, ba phân giác, hoặc
ba trung trực của một tam giác — chúng luôn đồng quy theo định lý đã học.

**Dấu hiệu nhận biết:** ba đường cùng xuất phát từ ba đỉnh hoặc cùng vuông góc
với ba cạnh.

**Các bước:** chỉ ra ba đường đó là ba đường đặc biệt của một tam giác cụ thể,
rồi kết luận đồng quy tại trực tâm / trọng tâm / tâm nội tiếp / tâm ngoại tiếp.

**Khi nào KHÔNG dùng:** khi ba đường không cùng loại (ví dụ một đường cao, một
trung tuyến, một phân giác) — chúng không đồng quy theo định lý nào cả.

**Bẫy thường gặp:**
- Không nêu rõ đang xét tam giác nào — nhiều bài phải nhận ra tam giác ẩn trong hình.
- Nhầm đường trung tuyến với đường trung trực (một đi qua đỉnh, một vuông góc tại trung điểm).
- Ba đường thuộc ba tam giác khác nhau — không áp dụng được.
- Với tam giác tù, trực tâm và tâm ngoại tiếp nằm ngoài tam giác; vẽ hình sai dẫn tới lập luận sai.


**Ví dụ:** Cho ΔABC, ba đường trung trực của ba cạnh đồng quy tại tâm đường tròn ngoại tiếp O. Nếu đề cho ba đường thẳng lần lượt vuông góc với BC tại trung điểm BC, với CA tại trung điểm CA, với AB tại trung điểm AB thì kết luận ngay chúng đồng quy tại O.

_Công cụ: T-TRIANGLE-CENTERS_

## Hướng 3 — Ba đường cùng đi qua tâm một đường tròn

**Khi nào dùng:** ba đường đều đi qua tâm (ví dụ ba đường kính, hoặc ba trung
trực của các dây).

**Khi nào KHÔNG dùng:** khi chưa chứng minh được cả ba đường đều đi qua tâm,
hoặc khi hình có nhiều đường tròn và tâm không thống nhất.

**Bẫy thường gặp:**
- Chứng minh hai đường qua tâm rồi mặc nhiên coi đường thứ ba cũng vậy.
- Nhầm tâm đường tròn ngoại tiếp với tâm nội tiếp khi hình có cả hai.
- Dùng cho đường tròn thay đổi theo điểm chạy — tâm không cố định.

---
### Ghi chú cho giáo viên
- Nhấn mạnh: KHÔNG dùng Ceva ở chế độ basic/exam10.

**Ví dụ:** Cho (O) và ba dây AB, CD, EF. Ba đường trung trực của ba dây này đều đi qua tâm O (vì O cách đều hai đầu mỗi dây), nên chúng đồng quy tại O.

