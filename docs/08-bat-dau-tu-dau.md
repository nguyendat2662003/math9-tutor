# 08 — Bắt đầu từ đâu

**Đừng viết dòng code sản phẩm nào trong tuần đầu.** Việc đầu tiên là đo xem
model hiện tại sai ở đâu, vì toàn bộ kiến trúc là phản ứng với các kiểu lỗi cụ
thể — mà bạn chưa biết kiểu lỗi nào thực sự xảy ra.

## Việc tuần đầu (5-7 ngày)

### 1. Tìm giáo viên — làm ngay hôm nay
Đường găng dài nhất của cả dự án. Cần giáo viên Toán THCS có kinh nghiệm luyện
thi vào 10, cam kết ≥ 10 giờ/tuần. Không có người này thì không chấm được lời
giải, không viết được sổ tay. Mọi việc khác chờ được, việc này không.

### 2. Gom 30 bài
Từ đề thi tuyển sinh 10 công khai của vài Sở. Phân bổ có chủ đích:

| Loại | Số bài |
|---|---|
| Đại số quen thuộc (rút gọn, PT bậc hai, Viète, lập PT) | 10 |
| Hình học cơ bản (tiếp tuyến, góc nội tiếp, tứ giác nội tiếp) | 10 |
| Hình học câu cuối (chứng minh khó, điểm cố định, cực trị) | 7 |
| Thống kê, xác suất | 3 |

30 là con số cố ý — đủ thấy quy luật, đủ ít để xong trong một tuần.

### 3. Chạy thủ công qua model API mạnh
Không RAG, không guardrail, không code. Chỉ dán đề vào chat với prompt tối giản:
"Giải bài toán sau theo chương trình Toán lớp 9 Việt Nam, trình bày như bài làm
của học sinh." Lưu toàn bộ đầu ra. Mục đích: lấy **baseline trần trụi**.

### 4. Giáo viên chấm theo 5 trục
Bảng có cấu trúc, không phải nhận xét chung chung:

| Trục | Câu hỏi | Ghi |
|---|---|---|
| Đáp án | Đúng/sai? | Đ/S |
| Lập luận | Bước nào hổng, thiếu xét trường hợp? | Đ/S + mô tả |
| Chương trình | Dùng kiến thức ngoài lớp 9? | Có/Không + tên |
| Trình bày | Giám khảo có cho điểm? | 0-2 |
| Hình vẽ | Mô tả hình đúng không? | Đ/S |

### 5. Tổng hợp một trang
Bao nhiêu phần trăm sai ở mỗi trục, sai kiểu gì. Đây là sản phẩm bàn giao duy
nhất của tuần đầu.

## Bảng đó quyết định thứ tự sprint

- **Trục chương trình hỏng nhiều** → guardrail + bản đồ chương trình lên số 1.
- **Trục đáp án hỏng ở đại số** → Verifier SymPy trước.
- **Trục lập luận hỏng ở hình khó** → sổ tay + kỹ thuật hai pha lên trước.
- **Chỉ trục trình bày hỏng** → may mắn, vá bằng few-shot, ra MVP sớm.

Kết quả sẽ khác dự đoán của bạn ở ít nhất một trục. Đó chính là lý do phải làm
bước này trước khi code.

## Bốn quyết định phải chốt trước khi viết agent

1. **Bộ sách chuẩn** — KNTT / CTST / Cánh diều? Ảnh hưởng trực tiếp bản đồ
   chương trình. Ba bộ khác thứ tự chương và cách phát biểu định lý.
2. **Mô hình kinh doanh** — miễn phí giới hạn / thuê bao / bán cho trường?
   Quyết định trần chi phí mỗi câu hỏi.
3. **Có phục vụ giáo viên (soạn đề, chấm) không?** Nếu có, ProblemState cần
   thiết kế mở rộng ngay.
4. **Ngưỡng độ trễ chấp nhận được** trên mobile mạng yếu.

## Sau tuần đầu

Kiểm tra scaffold chạy được:
```bash
make install && make test    # 37 test, ~0.4s
```

Rồi theo lộ trình `03`, ưu tiên điều chỉnh theo bảng 5 trục ở trên.

## Chi phí tuần đầu

Gần như bằng không. Thời gian: một tuần. Đổi lại: tránh xây nhầm thứ tự trong
ba tháng tiếp theo.
