# 04 — Công việc của giáo viên

Vai trò không thể thay thế bằng kỹ sư. Ba nhóm việc chính, xếp theo thứ tự.

## Vì sao cần giáo viên

Kỹ sư dựng được engine, verifier, RAG. Nhưng ba thứ sau chỉ giáo viên làm được,
và chúng quyết định chất lượng sản phẩm:

- **Ranh giới kiến thức** — công cụ nào được phép ở lớp 9, công cụ nào vượt cấp.
- **Chiến lược giải** — với mỗi loại mục tiêu, có những hướng nào, khi nào dùng.
- **Chấm chất lượng** — lời giải này có được giám khảo thi vào 10 chấp nhận không.

---

## Việc 1 — Bản đồ chương trình (Sprint 1)

Mỗi chương sách KNTT có một file YAML liệt kê công cụ được phép dùng. Đã soạn
đủ 10 file trong `data/curriculum/` (mã theo số chương: `ALG-1` … `GEO-10`).
Việc của giáo viên là **soát**, không phải viết từ đầu.

**Mỗi công cụ ghi rõ dùng được ở chế độ nào:**
- `basic` — đúng SGK, không hơn
- `exam10` — SGK + kỹ thuật thường gặp trong đề thi vào 10
- `advanced` — thêm phương tích, Ptolemy (học sinh giỏi)

Ví dụ: phương tích được `advanced` nhưng bị chặn ở `basic` và `exam10`.

**Cần làm:** với mỗi file, kiểm tra (a) `statement` có đúng cách phát biểu của
SGK KNTT không, (b) `modes` có đúng không — công cụ nào thực sự dạy ở lớp 9,
công cụ nào chỉ nên cho học sinh giỏi, (c) `aliases` có phủ cách bạn thường
viết căn cứ trong lời giải không (guardrail đối chiếu bằng chuỗi này).
Khoảng 30 phút/file.

**Đã chốt bộ sách:** Kết nối tri thức với cuộc sống. Bốn điểm còn phải xác nhận
nằm ở `data/methods/so-tay-toan-9/_BAN-DO-CHUONG-TRINH.md` — hai trong số đó
(góc tạo bởi tia tiếp tuyến và dây; quỹ tích) hiện tạm khóa ở `advanced`.

---

## Việc 2 — Sổ tay phương pháp (Sprint 1, song song việc 1)

Đây là khoản đầu tư giá trị cao nhất của dự án. Tổ chức theo **mục tiêu chứng
minh** (goal_type), không theo chương.

**Có hai cách làm:**

### Cách A — soạn từ đầu (4 tuần)
Viết 40-60 tài liệu, mỗi tài liệu cho một goal_type. Xem mẫu:
`data/methods/prove_concyclic.md`.

### Cách B — rút từ tài liệu có sẵn (1 tuần) ⭐ khuyên dùng
Pipeline `methods` biến tài liệu tra cứu (ví dụ "Cẩm nang Toán 9" 59 trang)
thành khung draft. LLM rút được các hướng và dấu hiệu nhận biết. Giáo viên chỉ
cần **soát và bổ sung hai thứ tài liệu không có:**

- **Khi nào KHÔNG dùng** hướng này
- **Bẫy thường gặp**

Cộng với gắn bài minh họa từ kho đề.

**Quy trình cách B:**
```
kỹ sư chạy build_methods → giáo viên nhận khung .md có sẵn phần rút được
→ điền 2 mục để trống, đổi status thành 'reviewed'
```

Chỗ cần điền hiện rõ dòng `_(giáo viên bổ sung)_` trong file. Chưa điền đủ thì
`gate_for_rag` chặn không cho vào hệ thống — bảo hiểm để sổ tay nửa vời không lọt.

**Vì sao không bỏ được bước giáo viên:** lời giải và tài liệu tra cứu chỉ cho
thấy con đường đã chọn, không cho thấy *vì sao chọn* và *đã loại bỏ hướng nào*.
Chính thông tin đó giúp Solver chọn đúng hướng cho bài mới.

---

## Việc 3 — Chấm eval (liên tục, từ Sprint 0)

Chấm lời giải của hệ thống theo 5 trục. Đây là cách duy nhất biết hệ thống
đang tốt lên hay tệ đi.

| Trục | Câu hỏi | Ghi |
|---|---|---|
| Đáp án | Đúng hay sai? | Đ/S |
| Lập luận | Có bước hổng, thiếu xét trường hợp? | Đ/S + mô tả |
| Chương trình | Có dùng kiến thức ngoài lớp 9? | Có/Không + tên công cụ |
| Trình bày | Giám khảo thi vào 10 có cho điểm? | 0-2 |
| Hình vẽ | Mô tả hình đúng quan hệ không? | Đ/S |

**Tuần đầu (Sprint 0):** chấm 30 bài do model API giải thô, để lấy baseline.
Đây là việc quan trọng nhất tuần đầu. Xem `08`.

**Về sau:** chấm mẫu 50 bài/tuần để theo dõi chất lượng.

### Công cụ hỗ trợ
- `tools/review_queue.py` xuất CSV mở bằng Excel, điền rồi nhập lại.
- Cột `predicates` quan trọng nhất: điền đúng thì hình vẽ được chấm **tự động**
  bằng Verifier, không cần nhìn bằng mắt.

---

## Lịch làm việc gợi ý

| Tuần | Việc |
|---|---|
| 1 | Chốt bộ sách. Chấm 30 bài baseline. |
| 2-3 | Bản đồ chương trình 17 file. Bắt đầu sổ tay (cách B). |
| 4-5 | Soát sổ tay: điền "khi nào không dùng" + "bẫy", gắn bài minh họa. |
| 6+ | Chấm eval mẫu hàng tuần. Bổ sung sổ tay cho goal_type còn thiếu. |

Tài liệu toanmath không phủ: thống kê, xác suất, quỹ tích — cần soạn riêng
hoặc tìm nguồn khác cho các goal_type này.
