---
goal_type: prove_equal_length
title_vi: Chứng minh hai đoạn thẳng bằng nhau, chứng minh hệ thức
topics: [GEO-4, GEO-5, GEO-9]
modes: [basic, exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Chứng minh hai đoạn thẳng bằng nhau, chứng minh hệ thức tích

> Gồm hai kiểu: hai đoạn bằng nhau (AB = CD) và hệ thức tích (MA·MB = MC·MD).
> Kiểu thứ hai rất hay gặp ở đề vào 10, giải bằng tam giác đồng dạng.

## Hướng 1 — Hai tam giác bằng nhau

**Khi nào dùng:** hai đoạn là cạnh tương ứng của hai tam giác chứng minh được
bằng nhau (c.c.c, c.g.c, g.c.g).

**Các bước:**
1. Chọn hai tam giác chứa hai đoạn đó làm cạnh tương ứng.
2. Chứng minh hai tam giác bằng nhau.
3. Suy ra hai cạnh tương ứng bằng nhau.

**Khi nào KHÔNG dùng:** khi hai đoạn không nằm ở vị trí cạnh tương ứng của hai
tam giác nào, hoặc khi bài yêu cầu hệ thức TÍCH — lúc đó phải dùng Hướng 3.

**Bẫy thường gặp:**
- Ghép sai cạnh tương ứng do viết sai thứ tự đỉnh khi khẳng định hai tam giác bằng nhau.
- Dùng "cạnh–cạnh–góc" — KHÔNG phải trường hợp bằng nhau hợp lệ.
- Chứng minh bằng ba góc bằng nhau — đó chỉ là đồng dạng, không phải bằng nhau.


**Ví dụ:** Cho (O), dây AB và dây CD bằng nhau. Gọi H, K là trung điểm AB, CD. Từ ΔOHA = ΔOKC (cạnh huyền – cạnh góc vuông) suy ra OH = OK.

_Công cụ: T-CONGRUENT-TRIANGLE_

## Hướng 2 — Tính chất hai tiếp tuyến cắt nhau

**Khi nào dùng:** hai đoạn là hai tiếp tuyến kẻ từ cùng một điểm ngoài đường tròn.

**Dấu hiệu nhận biết:** trong hình có một điểm ngoài đường tròn và hai tiếp
tuyến từ điểm đó.

**Các bước:**
1. Chỉ ra hai đoạn là hai tiếp tuyến từ cùng một điểm.
2. Áp dụng tính chất: hai tiếp tuyến cắt nhau thì bằng nhau.

**Khi nào KHÔNG dùng:** khi hai đoạn không phải tiếp tuyến từ cùng một điểm,
hoặc chưa chứng minh được chúng là tiếp tuyến.

**Bẫy thường gặp:**
- Áp dụng khi mới chỉ có MỘT tiếp tuyến, hoặc hai tiếp tuyến từ hai điểm khác nhau.
- Quên nêu điểm xuất phát nằm NGOÀI đường tròn.
- Nhầm tính chất này với tính chất đường nối tâm — hai kết luận khác nhau.


**Ví dụ:** Cho (O) và A nằm ngoài, hai tiếp tuyến AB, AC. Theo tính chất hai tiếp tuyến cắt nhau từ A, ta có AB = AC.

_Công cụ: T-TWO-TANGENTS_

## Hướng 3 — Tam giác đồng dạng suy ra hệ thức tích

**Khi nào dùng:** chứng minh hệ thức dạng MA·MB = MC·MD hoặc MA² = MB·MC. Đây
là hướng chủ đạo cho các hệ thức tích ở đề vào 10.

> ⚠ Ví dụ bên dưới dùng góc tạo bởi tia tiếp tuyến và dây. Nếu bộ sách không dạy
> định lý này, dùng Hướng 5. Đáp án chính thức của các đề 2026 đều không cần tới nó.

**Dấu hiệu nhận biết:** hệ thức có dạng tích hai đoạn bằng tích hai đoạn khác,
hoặc bình phương một đoạn bằng tích hai đoạn.

**Các bước:**
1. Từ hệ thức cần chứng minh, viết lại thành tỉ lệ thức (MA/MC = MD/MB).
2. Tìm hai tam giác nhận các đoạn đó làm cạnh, có chung một góc.
3. Chứng minh hai tam giác đồng dạng.
4. Suy ra tỉ lệ thức, biến đổi về hệ thức cần chứng minh.

**Khi nào KHÔNG dùng:** ở chế độ advanced có thể dùng phương tích cho nhanh,
nhưng ở basic và exam10 thì KHÔNG được — bắt buộc đi đường đồng dạng. Cũng khó
dùng khi hai đoạn không chung đỉnh nào.

**Bẫy thường gặp:**
- Viết tỉ lệ thức sai thứ tự: từ ΔMAC ~ ΔMDB phải suy MA/MD = MC/MB, không phải MA/MB = MC/MD.
- Không chỉ rõ góc chung hoặc góc đối đỉnh tại đỉnh M trước khi kết luận đồng dạng.
- Nhân chéo sai khi biến đổi từ tỉ lệ thức về hệ thức tích.
- Chọn nhầm cặp tam giác: nên viết hệ thức thành tỉ lệ TRƯỚC rồi mới tìm tam giác, đừng đoán mò.


**Ví dụ:** Cho (O) và A ngoài đường tròn, cát tuyến qua A cắt (O) tại M, N; tiếp tuyến AB. Chứng minh AB² = AM·AN: từ góc ABM = góc ANB (cùng chắn cung BM) và góc A chung, suy ra ΔABM ~ ΔANB, do đó AB/AN = AM/AB.

_Công cụ: T-SIMILAR-TRIANGLE_

## Hướng 4 — Hệ thức lượng trong tam giác vuông

**Khi nào dùng:** đoạn cần tính nằm trong tam giác vuông có đường cao, dùng được
b² = ab′, h² = b′c′, ah = bc.

**Khi nào KHÔNG dùng:** khi tam giác không vuông, hoặc vuông nhưng không có
đường cao ứng với cạnh huyền. Nhiều học sinh áp dụng nhầm cho tam giác thường.

**Bẫy thường gặp:**
- Xác định nhầm hình chiếu b′, c′ — phải là hình chiếu của cạnh góc vuông TRÊN CẠNH HUYỀN.
- Dùng h² = b′·c′ khi h không phải đường cao ứng với cạnh huyền.
- Quên kiểm tra tam giác có vuông không trước khi áp dụng.


**Ví dụ:** ΔABC vuông tại A, đường cao AH, biết BH = 4, CH = 9. Khi đó AH² = BH·CH = 36 nên AH = 6.

_Công cụ: T-RIGHT-TRIANGLE-RELATIONS_

## Hướng 5 — Hệ thức tiếp tuyến–cát tuyến chỉ dùng Pythagore

**Khi nào dùng:** chứng minh MA² = MB·MC, với MA là tiếp tuyến và đường thẳng
qua M cắt đường tròn tại B, C — mà KHÔNG cần tới góc tạo bởi tia tiếp tuyến và
dây. Đây là con đường an toàn nếu bộ sách không dạy định lý đó.

**Các bước:**
1. Gọi K là trung điểm BC. Vì OK đi qua tâm và qua trung điểm dây nên OK ⊥ BC.
2. MB·MC = (MK − KB)(MK + KB) = MK² − KB².
3. Pythagore trong hai tam giác vuông MKO và BKO: MK² = MO² − OK², KB² = R² − OK².
   Suy ra MB·MC = MO² − R².
4. Tam giác MAO vuông tại A (tiếp tuyến vuông góc bán kính): MA² = MO² − R².
5. Vậy MA² = MB·MC.

**Khi nào KHÔNG dùng:** khi bộ sách cho phép góc tạo bởi tia tiếp tuyến và dây —
Hướng 3 (đồng dạng) ngắn hơn. Nếu cát tuyến đi qua tâm thì K trùng O, lập luận
càng đơn giản.

**Bẫy thường gặp:**
- Viết MB = MK − KB mà chưa xác định B nằm giữa M và K.
- Quên chứng minh OK ⊥ BC trước khi dùng Pythagore.
- Trường hợp cát tuyến qua tâm (dây BC là đường kính) phải xét riêng vì "trung điểm dây" trùng tâm.

**Ví dụ (Hưng Yên 2026, câu Đúng/Sai 1b):** khẳng định IA² = IM.IN là ĐÚNG, và
chứng minh được hoàn toàn bằng các bước trên. Đã kiểm chứng bằng engine hình học
trên 5 cấu hình ngẫu nhiên.

**Ví dụ 2 (Hà Tĩnh 2026 câu 13b) — cát tuyến đi qua tâm:** AO cắt (O) tại P, Q.
Khi đó K trùng O, lời giải chỉ còn một dòng: AP·AQ = (AO − R)(AO + R) = AO² − R² = AM².
Lời giải bên thứ ba của đề này dùng góc tạo bởi tiếp tuyến và dây — dài hơn và có
thể nằm ngoài chương trình.

_Công cụ: T-PYTHAGORE, T-DIAMETER-CHORD, T-TANGENT-PERP_

---
### Ghi chú cho giáo viên
- Hướng 3 quan trọng nhất cho đề vào 10 — nên bổ sung nhiều bài minh họa.
- Lưu ý ranh giới chế độ: phương tích chỉ dùng ở advanced.
