# Hướng dẫn kiểm tra sổ tay Toán 9

**26 sổ tay · 103 hướng giải · phủ đủ 26 dạng mục tiêu**

> Cập nhật sau khi phân tích đề 2026: thêm sổ tay `evaluate_root_expression`, thêm
> Hướng 5 (Pythagore) cho `prove_equal_length`, thêm ghi chú hạ bậc cho `find_parameter`.
>
> Cập nhật đợt 2 (thêm 6 đề): `evaluate_root_expression` thêm Hướng 4 và ví dụ Nghệ An;
> `find_max_min` thêm Hướng 5 (thể tích — phân tích nghiệm kép) và Hướng 6 (ràng buộc
> số nguyên); `prove_equal_length` thêm ví dụ Hà Tĩnh.
Bám bộ **Kết nối tri thức với cuộc sống** (GDPT 2018), phủ đủ 10 chương.

## Sổ tay đã ĐẦY ĐỦ — việc của bạn là kiểm tra

Mỗi hướng giải có đủ bốn phần:

- Khi nào dùng, dấu hiệu nhận biết
- **Khi nào KHÔNG dùng**
- **Bẫy thường gặp**
- **Ví dụ minh họa** có lời giải

Các ví dụ số học đã được kiểm chứng bằng SymPy (giải lại độc lập, khớp 100%).
Phần hình học kiểm chứng bằng engine dựng hình trên 5 cấu hình ngẫu nhiên.

**Nhưng máy chỉ kiểm được tính đúng của phép tính và kết luận.** Ba thứ máy
KHÔNG kiểm được, cần người đọc:

1. Căn cứ nêu ra có thuộc phạm vi lớp 9 theo SGK đang dùng không.
2. Lỗi liệt kê có đúng là lỗi học sinh Việt Nam hay mắc không.
3. Cách diễn đạt có khớp văn phong SGK và cách chấm thi không.

## Ba việc với mỗi file

### 1. Đọc và xác nhận nội dung

Với mỗi mục "Khi nào KHÔNG dùng", "Bẫy thường gặp", "Ví dụ":

- Đúng và đủ, giữ nguyên
- Đúng nhưng thiếu, bổ sung lỗi bạn thực tế hay thấy học sinh mắc
- Sai hoặc không hợp bộ sách, sửa lại

### 2. (Tùy chọn) Thay ví dụ bằng bài từ đề thi thật

Ví dụ hiện tại là bài tự soạn, đủ minh họa nhưng chưa gắn nguồn. Nếu muốn, thay
bằng bài đề vào 10 và ghi mã: `_Bài minh họa: hn-2024-c4b_`

### 3. Đổi trạng thái khi xong

```
status: needs_teacher   ->   status: reviewed
```

Hệ thống chỉ nạp sổ tay `reviewed` vào RAG.

## Cách kiểm tra nhanh

Với mỗi file, đọc theo thứ tự này, dừng khi thấy bất thường:

1. **Frontmatter** — `topics` có khớp chương KNTT không?
2. **Lướt tên các hướng** — có hướng nào bạn hay dạy mà thiếu không?
3. **Đọc kỹ mục "Bẫy thường gặp"** — phần dễ sai nhất vì phụ thuộc thực tế lớp học.
4. **Kiểm tra ví dụ** — phép tính đã đúng, nhưng cách TRÌNH BÀY có đúng chuẩn
   chấm thi không?

## Bốn điểm về chương trình cần xác nhận TRƯỚC

Xem `_BAN-DO-CHUONG-TRINH.md`. Tóm tắt:

1. **Góc tạo bởi tia tiếp tuyến và dây** — mục lục KNTT Chương IX không có bài
   riêng. Còn dạy không? Ảnh hưởng trực tiếp tới guardrail. Sổ tay `prove_similar`
   có một ví dụ dùng định lý này, đã đánh dấu cần kiểm tra.
2. **Quỹ tích** — không thấy trong mục lục. `find_locus` tạm để `advanced`.
3. **Phương trình trùng phương** — không có bài riêng. Còn trong chuẩn không?
   (`solve_equation` Hướng 5 có dạng này.)
4. **Xác suất (Chương VIII)** — dạy tới đâu? Có biến cố hợp và giao không?

## Thứ tự kiểm tra ưu tiên

### Nhóm 1 — Xuất hiện nhiều nhất ở đề vào 10

`prove_concyclic` · `find_parameter` · `evaluate_root_expression` · `prove_equal_length` ·
`simplify_expression` · `solve_equation`

### Nhóm 2 — Nội dung MỚI của GDPT 2018, nên đối chiếu SGK kỹ

| Sổ tay | Chương | Ghi chú |
|---|---|---|
| `analyze_statistics` | VII | Mới hoàn toàn |
| `compute_probability` | VIII | Mới hoàn toàn, cần xác nhận phạm vi |
| `prove_inequality` | II | Chuyển từ lớp 8 xuống |

### Nhóm 3 — Dạng khó (câu cuối đề thi)

`find_fixed_point` · `prove_collinear` · `prove_concurrent` · `find_max_min`

### Nhóm 4 — Còn lại

`prove_equal_angle` · `prove_perpendicular` · `prove_parallel` · `prove_midpoint` ·
`prove_similar` · `compute_angle` · `compute_length` · `compute_area` ·
`analyze_function` · `solve_system` · `word_problem` · `prove_tangent` · `find_locus`

## Bảng đối chiếu chương KNTT với sổ tay

| Chương | Sổ tay liên quan |
|---|---|
| I. Hệ hai PT bậc nhất hai ẩn | `solve_system`, `word_problem` |
| II. PT và BPT bậc nhất một ẩn | `solve_equation`, `prove_inequality` |
| III. Căn bậc hai, căn bậc ba | `simplify_expression`, `solve_equation` |
| IV. Hệ thức lượng tam giác vuông | `compute_length`, `compute_angle`, `prove_similar` |
| V. Đường tròn | `prove_tangent`, `prove_midpoint`, `compute_area`, `compute_length` |
| VI. Hàm số bậc hai và phương trình bậc hai | `analyze_function`, `find_parameter`, `solve_equation`, `word_problem` |
| VII. Tần số, tần số tương đối | `analyze_statistics` |
| VIII. Xác suất | `compute_probability` |
| IX. Đường tròn ngoại tiếp và nội tiếp | `prove_concyclic`, `prove_equal_angle`, `prove_collinear`, `prove_concurrent` |
| X. Hình khối thực tiễn | `compute_area` |

## Ước lượng thời gian

- Nhóm 1 (5 file): khoảng 2 giờ
- Nhóm 2 (3 file): khoảng 2,5 giờ
- Nhóm 3 (4 file): khoảng 2 giờ
- Nhóm 4 (13 file): khoảng 3,5 giờ

**Tổng khoảng 10 giờ**, tức 2 buổi làm việc.
