# Bản đồ chương trình — bộ Kết nối tri thức với cuộc sống (KNTT)

Mã chuyên đề căn theo đúng số chương của sách, dễ đối chiếu.

| Mã | Chương | Bài | Nội dung |
|---|---|---|---|
| ALG-1 | I | 1–3 | Phương trình và hệ hai phương trình bậc nhất hai ẩn |
| ALG-2 | II | 4–6 | Phương trình quy về bậc nhất một ẩn; bất đẳng thức; bất phương trình |
| ALG-3 | III | 7–10 | Căn bậc hai, căn bậc ba |
| GEO-4 | IV | 11–12 | Hệ thức lượng trong tam giác vuông |
| GEO-5 | V | 13–17 | Đường tròn: cung, dây, độ dài cung, vị trí tương đối |
| ALG-6 | VI | 18–21 | Hàm số bậc hai; phương trình bậc hai; định lí Viète |
| STA-7 | VII | 22–24 | Tần số và tần số tương đối |
| PRO-8 | VIII | 25–26 | Xác suất của biến cố |
| GEO-9 | IX | 27–30 | Góc nội tiếp; đường tròn ngoại tiếp và nội tiếp; tứ giác nội tiếp; đa giác đều |
| GEO-10 | X | 31–32 | Hình trụ, hình nón, hình cầu |

## Bốn điểm cần xác nhận

Đây là những khác biệt nhận thấy khi đối chiếu mục lục KNTT với chương trình cũ
(2006). Chúng ảnh hưởng trực tiếp tới guardrail — công cụ nào được phép dùng —
nên cần xác nhận trước khi chốt.

### 1. Góc tạo bởi tia tiếp tuyến và dây cung

Mục lục Chương IX chỉ có: Góc nội tiếp (B27), Đường tròn ngoại tiếp và nội tiếp
tam giác (B28), Tứ giác nội tiếp (B29), Đa giác đều (B30). Không thấy bài riêng
về góc tạo bởi tia tiếp tuyến và dây — vốn có ở chương trình cũ và rất hay dùng
trong đề thi.

**Cần xác nhận:** định lý này còn được dạy không? Nếu không, phải chuyển sang
`modes: [advanced]` trong bản đồ chương trình, và Solver không được dùng nó ở
chế độ basic hoặc exam10.

Sổ tay `prove_similar.md` hiện có một ví dụ dùng định lý này, đã đánh dấu cần
kiểm tra.

### 2. Góc ở tâm và số đo cung

Nằm ở Chương V Bài 14 (Cung và dây), không phải Chương IX như chương trình cũ.

**Ảnh hưởng:** thứ tự tiên quyết — khi dạy góc nội tiếp (B27) thì góc ở tâm đã
học từ B14.

### 3. Bất đẳng thức và bất phương trình (Chương II)

Nội dung này ở chương trình cũ thuộc lớp 8, nay chuyển xuống lớp 9.

**Ảnh hưởng:** cần sổ tay riêng cho `prove_inequality`, không coi là kiến thức
đã biết từ trước. Đã soạn.

### 4. Phương trình trùng phương

Không có bài riêng trong mục lục. Cần xác nhận dạng này còn nằm trong chuẩn kiến
thức không. Sổ tay `solve_equation.md` Hướng 5 có đề cập.

## Ghi chú về mã chuyên đề

Các sổ tay đang tham chiếu tới 23 mã công cụ (`T-VIETE`, `T-CYC-SAME-SIDE`,
`T-SIMILAR-AA`...). Những mã này cần tồn tại trong file YAML bản đồ chương trình
thì guardrail mới đối chiếu được. Đây là việc tiếp theo cần làm.
