# Frontend

Next.js 15 (App Router), TypeScript, không dùng framework CSS.

Ứng dụng độc lập — không cần mã của `backend/`, chỉ cần API của nó đang chạy.

```bash
cd frontend && npm install
npm run dev            # http://localhost:3000 — cần API chạy ở :8000 (cd backend && make api)
npm run typecheck
npm run build && npm run start   # bản production
```

## Biến môi trường (xem `.env.example`)

| Biến | Ý nghĩa |
|---|---|
| `NEXT_PUBLIC_API_URL` | Địa chỉ API mà trình duyệt gọi. Không đặt = `http://localhost:8000`. Đặt **chuỗi rỗng** khi dùng proxy bên dưới. Nhúng vào bundle lúc build — đổi thì build lại. |
| `BACKEND_URL` | Bật proxy: Next.js chuyển `/api/*` sang `${BACKEND_URL}/api/*` (`next.config.ts`). Cookie đăng nhập khi đó cùng tên miền với frontend. |

## Deploy lên Vercel

1. Import repo, **Root Directory = `frontend`**.
2. Environment Variables: `BACKEND_URL=https://<backend>` và `NEXT_PUBLIC_API_URL=` (rỗng).
3. Không dùng proxy (gọi thẳng `NEXT_PUBLIC_API_URL=https://<backend>`) thì backend phải đặt
   `CORS_ORIGINS=https://<frontend>` và `COOKIE_SAMESITE=none`.

## Ba yêu cầu giao diện đặc thù — đã làm

**Hình đồng bộ với bước giải.** Di chuột/chạm vào một bước → tô sáng các đối tượng
tương ứng trên hình, làm mờ phần còn lại. Engine bọc mỗi đối tượng SVG trong
`<g data-name data-kind data-pts>`; `components/figure/Figure.tsx` khớp
`Step.highlight` (hoặc `refs`) với các thuộc tính đó. Đây là điểm khác biệt sư
phạm lớn nhất so với các sản phẩm hiện có.

**Chế độ gợi ý là MẶC ĐỊNH.** `SolutionView` che lời giải, hiện `hints` trước;
học sinh bấm "Em đã thử — xem lời giải" mới mở. Có thể tắt gợi ý ở ô nhập
(khi đó lời giải hiện ngay).

**Nhãn độ tin cậy.** `ConfidenceBadge` luôn hiện, đổi màu theo `confidence`,
kèm lý do (SymPy khớp, hình đúng n/5 cấu hình, kết luận sai, vượt chương trình).

## Cấu trúc
```
app/page.tsx                 màn hình chính: nhập đề → tiến trình SSE → kết quả
components/
  chat/ProblemInput.tsx      ô nhập, chế độ, bài mẫu
  chat/StageProgress.tsx     tiến trình theo sự kiện SSE (kể cả lần giải lại)
  solution-view/             gợi ý, các bước, đáp án, nhãn độ tin cậy
  figure/Figure.tsx          SVG + tô sáng theo bước
  MathText.tsx               KaTeX cho $...$ (dự phòng; Solver xuất Unicode)
lib/api.ts                   client SSE (stage / done / error)
types/state.ts               phản chiếu ProblemState — giữ đồng bộ với state.py
```

**Gửi ảnh đề bài.** `components/chat/ImagePicker.tsx`: bấm chọn file, kéo-thả,
hoặc dán bằng Ctrl+V (nhanh nhất khi chụp màn hình đề). Ảnh đi qua
`POST /api/upload` → nhận `image_id` → `POST /api/solve` kèm id đó. Đề đọc được
từ ảnh hiện ngay trong khung tiến trình để học sinh đối chiếu trước khi tin lời giải.

**Luyện đề** (`app/exam/page.tsx`): chọn đề theo tỉnh hoặc tự chọn → làm bài có đồng hồ →
nộp → kết quả kèm đáp án, lời giải, tự chấm câu chứng minh. Bài đang làm lưu trong
`localStorage` (chỉ id đề và câu trả lời, không có đáp án). Component ở `components/exam/`.
Kiểm tra toàn luồng: `node e2e/browser_exam_check.mjs` (chạy trong `frontend/`).

## Chưa làm
- MathLive (bàn phím toán ảo) — hiện là textarea thường.
- JSXGraph tương tác — hiện là SVG tĩnh có tô sáng; đủ cho yêu cầu đồng bộ bước.
