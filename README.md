# Math9 Tutor

> **AI tutor for Vietnamese 9th-grade math** — solves algebra and geometry problems step by step, draws accurate figures, and *verifies every answer with code, not with another LLM*.

**Trợ lý học Toán lớp 9 (chương trình GDPT 2018):** học sinh gõ đề hoặc chụp ảnh đề, nhận gợi ý từng bước, lời giải có căn cứ và hình vẽ chính xác. Điểm khác biệt: mọi lời giải đều được **kiểm chứng tự động bằng SymPy và engine hình học**, và hệ thống nói rõ khi nó *không chắc* thay vì trả lời sai một cách tự tin.

## Tính năng

- **Giải bài đại số và hình học** từ chữ hoặc ảnh chụp đề; lời giải từng bước, mỗi bước nêu căn cứ.
- **Hình vẽ đồng bộ với lời giải:** rê chuột vào một bước thì các đối tượng liên quan được tô sáng trên hình.
- **Chế độ gợi ý mặc định:** hiện gợi ý trước, học sinh tự thử rồi mới mở lời giải.
- **Nhãn độ tin cậy** cho mỗi lời giải (đã kiểm chứng / một phần / chưa chắc).
- **Hỏi thêm sau khi giải:** chat streaming, trả lời bám đúng lời giải vừa xem.
- **Luyện đề thi vào 10:** sinh đề theo cấu trúc của 6 tỉnh hoặc tự chọn chuyên đề, làm có đồng hồ, chấm tự động.
- **Gợi ý bài tương tự** bằng tìm kiếm vector trên kho đề (Qdrant).
- **Quản trị:** một tài khoản admin cấp tài khoản cho học sinh; tải đề PDF/Word/ảnh lên, LLM tách bài, giáo viên duyệt rồi mới vào kho.
- **Lịch sử học tập** từng học sinh, giới hạn lượt dùng mỗi ngày, theo dõi chi phí và chất lượng LLM bằng Langfuse.

## Điểm đáng chú ý về kỹ thuật

1. **LLM không bao giờ sinh tọa độ.** LLM chỉ viết *kịch bản dựng hình* khai báo; engine hình học tính tọa độ bằng công thức, nên quan hệ hình học đúng ở độ chính xác máy. Đây là chỗ nhiều dự án tương tự thất bại.
2. **Kiểm chứng bằng code, không bằng LLM.** Hai LLM kiểm tra lẫn nhau thường sai giống nhau. Ở đây SymPy giải lại độc lập, còn engine dựng lại hình trên 5 cấu hình ngẫu nhiên và kiểm tra từng mệnh đề bằng số.
3. **Biết giới hạn của mình.** Vòng giải ↔ kiểm chứng tối đa 2 lần; sau đó trả phần đã chắc kèm nhãn độ tin cậy. Chỉ số quan trọng nhất của bộ đánh giá là **"sai mà tự tin"**.
4. **Bám chương trình lớp 9.** Định lý và công cụ được phép dùng nằm trong dữ liệu có cấu trúc (YAML), code kiểm tra lời giải có dùng kiến thức ngoài chương trình hay không (guardrail).
5. **Pipeline cố định, đo được.** Toán lớp 9 là miền đóng nên dùng đồ thị xử lý cố định thay vì agent tự quyết gọi nhau; Solver và Draftsman chạy song song.
6. **Có bộ đánh giá nghiêm túc.** Bộ đề thi thật có nhãn, chấm đáp án tự động bằng SymPy, và bộ **golden 153 bài** đã được giải lại độc lập ([chi tiết](backend/data/eval/README.md)). Hơn 300 test chạy không cần gọi LLM.

## Công nghệ

| Lớp | Công nghệ |
|---|---|
| Backend | Python 3.11+, FastAPI (SSE streaming), Pydantic, SQLAlchemy |
| Toán và hình học | SymPy, NumPy/SciPy, engine dựng hình riêng (DSL → tọa độ → SVG) |
| LLM | Giao thức OpenAI (mặc định `gpt-4.1-mini`, đổi được qua biến môi trường); đọc ảnh đề bằng VLM |
| Dữ liệu | PostgreSQL (Supabase), Qdrant Cloud, embedding `text-embedding-3-small` |
| Frontend | Next.js 15, React, TypeScript, KaTeX |
| Quan sát và kiểm thử | Langfuse, pytest, kiểm tra giao diện bằng trình duyệt headless |
| Triển khai | Docker (Render/Railway/Fly.io), Vercel |

## Kiến trúc

```
Parser → Router → { Solver ∥ Draftsman } → Verifier → [Critic] → Render → Pedagogue
                        ↑                       │
                        └──── giải lại (tối đa 2) ┘
```

| Agent | Vai trò |
|---|---|
| Parser | Đọc đề từ ảnh (VLM) |
| Router | Phân loại chuyên đề và dạng bài (`goal_type`), tách theo từng ý |
| Solver | Viết lời giải từng bước, kèm mệnh đề để kiểm chứng |
| Draftsman | Sinh kịch bản dựng hình (không sinh tọa độ) |
| Verifier | SymPy + dựng lại hình trên 5 cấu hình; đối chiếu chéo lời giải và hình |
| Critic | Biến kết quả kiểm chứng thành thông điệp sửa lỗi cụ thể cho Solver (không gọi LLM) |
| Pedagogue | Biến lời giải đã kiểm chứng thành chuỗi gợi ý |

## Chạy thử

**Cần:** Python 3.11+, Node.js 20+ và một API key OpenAI (hoặc model local theo giao thức OpenAI).

```bash
# 1. Backend
cd backend
pip install -e ".[dev]"
cp .env.example .env              # điền OPENAI_API_KEY (Windows: copy .env.example .env)
python tools/create_admin.py      # tạo tài khoản admin, in mật khẩu tạm
python -m uvicorn api.main:app --port 8000

# 2. Frontend (terminal khác)
cd frontend
npm install
npm run dev
```

Mở http://localhost:3000, đăng nhập `admin` bằng mật khẩu tạm (lần đầu sẽ được yêu cầu đổi), rồi gõ đề hoặc gửi ảnh đề.
Vào **Quản trị → Học sinh** để tạo tài khoản cho học sinh. Không đặt `DATABASE_URL` thì dữ liệu lưu ở SQLite
cục bộ, đủ để chạy thử.

```bash
cd backend && pytest -q                                   # chạy test, không cần LLM
python tools/solve.py "Giải phương trình x^2 - 5x + 6 = 0."   # giải một bài trên dòng lệnh
python evals/run.py --set smoke --limit 5                 # chạy thử bộ đánh giá (có gọi LLM, tốn chi phí)
```

> **Windows:** luôn chạy `python -m uvicorn ...` (không gõ `uvicorn` trần), và dùng `;` thay `&&` trong PowerShell 5.1.

Tùy chọn: Supabase (`DATABASE_URL`), Qdrant (`QDRANT_URL`, `QDRANT_API_KEY`), Langfuse — xem [`backend/.env.example`](backend/.env.example).
Hướng dẫn triển khai chi tiết: [`backend/README.md`](backend/README.md) (Docker, Render) và [`frontend/README.md`](frontend/README.md) (Vercel).

## Cấu trúc thư mục

```
backend/
  api/          FastAPI: giải bài, luyện đề, tài khoản, lịch sử, quản trị
  packages/     geometry (engine dựng hình) · verifier (SymPy, kiểm chứng hình) · core (pipeline, agent)
                curriculum (guardrail) · retrieval (RAG) · exam (luyện đề) · accounts · ingest
  data/         chương trình YAML, sổ tay phương pháp, bộ đánh giá (core / hard / golden), cấu trúc đề theo tỉnh
  evals/        chạy đánh giá và chấm tự động
  tests/        test không cần LLM
frontend/       Next.js: giải bài, luyện đề, lịch sử, quản trị
docs/           tài liệu thiết kế chi tiết (kiến trúc, RAG, đánh giá, rủi ro)
```

Thiết kế chi tiết: [`docs/`](docs/README.md).
