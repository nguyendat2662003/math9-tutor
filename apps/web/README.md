# Frontend

Next.js 15 (App Router). Chưa dựng UI — đây là khung thư mục và tầng dữ liệu.

## Thư viện
| Việc | Thư viện |
|---|---|
| Render công thức | KaTeX |
| Nhập công thức | MathLive (bàn phím toán ảo — quan trọng trên mobile) |
| Hình học tương tác | JSXGraph |
| Luồng phản hồi | SSE (native EventSource / fetch stream) |

## Ba yêu cầu giao diện đặc thù

**Hình đồng bộ với bước giải.** Hover hoặc chạm vào một bước → tô sáng các đối
tượng tương ứng trên hình. Dùng trường `highlight` trong `Step`. Đây là điểm
khác biệt sư phạm lớn nhất so với các sản phẩm hiện có.

**Chế độ gợi ý là MẶC ĐỊNH.** Che đáp án, hiện `hints` trước. Học sinh bấm
"xem lời giải" mới mở. Đây là yêu cầu sư phạm, không phải tùy chọn — một
chatbot giải sẵn bài tập sẽ bị giáo viên phản đối và làm học sinh học kém đi.

**Nhãn độ tin cậy.** Khi `confidence !== "high"`, hiển thị rõ ràng, không giấu.
Trả lời sai một cách tự tin là lỗi tệ nhất mà sản phẩm này có thể mắc.

## Cấu trúc
```
app/                 route + layout
components/
  chat/              khung hội thoại, bong bóng tin nhắn
  math-input/        MathLive wrapper, bàn phím toán
  solution-view/     danh sách bước + KaTeX + nhãn độ tin cậy
  figure/            JSXGraph wrapper, đồng bộ highlight theo bước
lib/api.ts           client SSE
types/state.ts       phản chiếu ProblemState
```
