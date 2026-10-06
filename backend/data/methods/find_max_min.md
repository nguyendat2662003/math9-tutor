---
goal_type: find_max_min
title_vi: Tìm giá trị lớn nhất, nhỏ nhất
topics: [ALG-2, ALG-3, ALG-6, GEO-5]
modes: [exam10]
status: needs_teacher
provenance: Soạn theo KNTT (GDPT 2018) — cần giáo viên xác nhận
---
# Tìm giá trị lớn nhất, nhỏ nhất

> Dạng khó, hay ở ý cuối. Lớp 9 KHÔNG dùng đạo hàm — chỉ biến đổi đại số và
> bất đẳng thức Cô-si.

## Hướng 1 — Đưa về dạng bình phương (hằng đẳng thức)

**Khi nào dùng:** biểu thức bậc hai. A = (…)² + k thì min A = k; A = k − (…)²
thì max A = k.

**Các bước:** biến đổi về bình phương đủ → đánh giá dấu → chỉ rõ dấu bằng xảy ra
khi nào (BẮT BUỘC).

**Khi nào KHÔNG dùng:** khi biểu thức không phải bậc hai, hoặc có mẫu chứa ẩn —
lúc đó thử Cô-si hoặc Hướng 3.

**Bẫy thường gặp:**
- Quên chỉ ra điều kiện dấu bằng — mất điểm dù kết quả đúng.
- Không kiểm tra giá trị làm dấu bằng có thỏa điều kiện xác định không.
- Tách bình phương sai (quên nhân hệ số a khi a ≠ 1).
- Kết luận "GTNN là k" mà không nói "đạt được khi x = ...".

**Ví dụ:** Tìm GTNN của A = x² − 4x + 7. Ta có A = (x−2)² + 3 ≥ 3. Dấu bằng khi x = 2. Vậy GTNN của A bằng 3 tại x = 2.

## Hướng 2 — Bất đẳng thức Cô-si cho hai số không âm

**Khi nào dùng:** tổng của hai số dương mà tích không đổi (hoặc ngược lại).
Dạng kinh điển: x + 1/x ≥ 2.

**Các bước:** kiểm tra điều kiện không âm → áp dụng a + b ≥ 2√(ab) → chỉ rõ dấu
bằng khi a = b.

**Khi nào KHÔNG dùng:** khi có số âm; khi tích hai số không cố định thì áp dụng
trực tiếp không cho kết quả có ý nghĩa (phải tách khéo trước).

**Bẫy thường gặp:**
- Áp dụng cho số có thể âm.
- Tách biểu thức sao cho tích không cố định — bất đẳng thức vẫn đúng nhưng không tìm được cực trị.
- Dấu bằng xảy ra tại giá trị nằm ngoài miền xác định — khi đó GTNN không đạt được, phải tìm cách khác.
- Cộng nhiều bất đẳng thức nhưng dấu bằng của chúng không đồng thời xảy ra.


**Ví dụ:** Tìm GTNN của B = x + 1/x với x > 0. Theo Cô-si: B ≥ 2√(x·1/x) = 2. Dấu bằng khi x = 1/x, tức x = 1. Vậy GTNN của B bằng 2 tại x = 1.

_Công cụ: T-AM-GM-2_

## Hướng 3 — Dùng điều kiện có nghiệm của phương trình bậc hai

**Khi nào dùng:** đặt y = biểu thức, đưa về phương trình bậc hai ẩn x tham số y,
rồi dùng Δ ≥ 0 tìm khoảng giá trị của y.

**Khi nào KHÔNG dùng:** khi không đưa được về phương trình bậc hai theo x, hoặc
khi hệ số bậc hai chứa y và có thể bằng 0 (phải xét riêng).

**Bẫy thường gặp:**
- Quên xét trường hợp hệ số bậc hai bằng 0.
- Tìm được khoảng giá trị của y nhưng quên tìm x tương ứng khi đạt cực trị.
- Không kiểm tra x tìm được có thỏa điều kiện ban đầu không.

**Ví dụ:** Tìm tập giá trị của y = (x²+1)/x với x > 0. Đưa về x²  − yx + 1 = 0. Để có nghiệm x thì Δ = y² − 4 ≥ 0, suy ra y ≥ 2 (do x > 0). Vậy GTNN của y bằng 2.

## Hướng 4 — Bài toán cực trị hình học

**Khi nào dùng:** tìm vị trí điểm để độ dài/diện tích lớn nhất.

**Mẹo:** thường quy về bất đẳng thức tam giác, quan hệ đường vuông góc ngắn nhất,
hoặc dây lớn nhất là đường kính.

**Khi nào KHÔNG dùng:** khi bài quy về được biểu thức đại số rõ ràng — lúc đó
dùng Hướng 1 hoặc 2 chặt chẽ hơn.

**Bẫy thường gặp:**
- Chỉ ra giá trị cực trị mà quên xác định VỊ TRÍ điểm đạt cực trị.
- Kết luận từ hình vẽ trực quan mà không chứng minh.
- Quên xét giới hạn chuyển động của điểm (điểm chỉ chạy trên một cung, không phải cả đường tròn).

**Ví dụ:** Cho (O; R) và dây AB chạy trên đường tròn. Dây AB lớn nhất khi AB là đường kính, khi đó AB = 2R. Đây là dạng cực trị hình học quy về nhận xét: trong một đường tròn, dây lớn nhất là đường kính.

## Hướng 5 — Cực trị bài toán thể tích: phân tích có nghiệm kép

> Bổ sung sau khi phân tích đề 2026: cực trị gắn với thực tế xuất hiện ở 5/8 đề phổ
> thông; riêng dạng thể tích lớn nhất có ở Nghệ An và Hà Tĩnh.

**Khi nào dùng:** thể tích (hoặc diện tích) quy về hàm bậc ba một biến, ví dụ
V = π(36 − h²)h hoặc V = (π/3)h²(12 − h), cần tìm giá trị lớn nhất.

**Ý tưởng:** đoán điểm đạt cực trị h₀ (thử vài giá trị, hoặc từ điều kiện dấu bằng),
rồi chứng minh Vmax − V(h) = (h − h₀)²·(biểu thức dương) ≥ 0. Chỉ cần phân tích
nhân tử, không cần bất đẳng thức nhiều số.

**Các bước:**
1. Lập V theo một biến, nêu miền giá trị (ví dụ 0 < h < 6).
2. Dự đoán h₀ và Vmax.
3. Phân tích Vmax − V(h) thành (h − h₀)²(h + c) với h + c > 0 trên miền.
4. Kết luận và nêu rõ đạt tại h = h₀.

**Khi nào KHÔNG dùng:** khi đã được phép dùng Cô-si cho ba số — cách đó ngắn hơn.
Lời giải bên thứ ba cho các đề này đều dùng Cô-si ba số; cần giáo viên xác nhận
Cô-si ba số có nằm trong chương trình lớp 9 không.

**Bẫy thường gặp:**
- Quên miền giá trị của biến (h phải nhỏ hơn đường sinh, nhỏ hơn đường kính...).
- Đoán sai h₀ thì không phân tích được thành bình phương — thử lại h₀.
- Tìm được Vmax nhưng quên tính kích thước tương ứng khi đề hỏi.

**Ví dụ 1 (Nghệ An 2026):** hình trụ chứa hình nón có đường sinh 6 cm, V = π(36 − h²)h.
Dự đoán h₀ = 2√3, Vmax = 48√3π. Ta có 48√3 − (36h − h³) = (h − 2√3)²(h + 4√3) ≥ 0.
**Ví dụ 2 (Hà Tĩnh 2026):** nón nội tiếp mặt cầu bán kính 6, V = (π/3)h²(12 − h).
Dự đoán h₀ = 8, Vmax = 256π/3. Ta có 256 − (12h² − h³) = (h − 8)²(h + 4) ≥ 0.

## Hướng 6 — Cực trị khi biến phải là số nguyên

**Khi nào dùng:** bài thực tế mà ẩn là số người, số ngày, kích thước tự nhiên.

**Ý tưởng:** Cô-si hoặc hằng đẳng thức cho điểm đạt cực trị có thể KHÔNG nguyên.
Khi đó phải xét các giá trị nguyên lân cận, thường là các ước của một số cho trước.

**Khi nào KHÔNG dùng:** khi điểm đạt cực trị liên tục đã là số nguyên — kết luận luôn.

**Bẫy thường gặp:**
- Kết luận theo Cô-si mà quên dấu bằng xảy ra tại giá trị không nguyên.
- Quên rằng biến còn phải là ước của tổng (ví dụ xy = 200 thì x phải là ước của 200).

**Ví dụ (Hà Nội 2026):** chi phí T = 3x + 200/x với x, 200/x nguyên dương. Cô-si cho
dấu bằng tại x = √(200/3) ≈ 8,16 — không nguyên. Xét các ước của 200 gần đó: x = 8
cho T = 49 nhỏ nhất (Thanh Hóa 2026 câu 15b cùng dạng, với ước của 67500).
