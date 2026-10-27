# Math9 Tutor

Chatbot giải toán lớp 9 (Đại số + Hình học) bám chương trình GDPT 2018, có vẽ hình.

Dự án tách thành **hai phần độc lập**, deploy riêng:

| Thư mục | Nội dung | Deploy gợi ý |
|---|---|---|
| [`backend/`](backend/README.md) | API FastAPI + toàn bộ engine Python (agent, verifier, dựng hình, dữ liệu, test) | Docker: Render / Railway / Fly.io |
| [`frontend/`](frontend/README.md) | Giao diện Next.js | Vercel (Root Directory = `frontend`) |

## Trạng thái

| Phần | Trạng thái |
|---|---|
| Engine dựng hình (`backend/packages/geometry`) | **Chạy được, có test** |
| Verifier hình học + đại số (`backend/packages/verifier`) | **Chạy được, có test** |
| Guardrail chương trình (`backend/packages/curriculum`) | **Chạy được, có test** — 10 file YAML chờ giáo viên soát |
| `ProblemState`, orchestrator (`backend/packages/core`) | **Chạy end-to-end với LLM thật** |
| Agent (Parser/Router/Solver/Draftsman/Critic/Pedagogue) | **Đủ 6 agent**; Parser đọc đề từ ảnh |
| API (FastAPI + SSE), frontend (Next.js) | **MVP chạy được** |
| Luyện đề thi vào 10 (`backend/packages/exam`) | **Chạy được, có test** — 6 cấu trúc tỉnh + tự chọn, chấm tự động |

Chi tiết từng package: [`docs/02-cong-viec-theo-package.md`](docs/02-cong-viec-theo-package.md).

## Cách chạy

### 1. Yêu cầu

- Python **3.11+** (đang dùng 3.14)
- Node.js **20+** (chỉ cần cho giao diện web)
- API key của một model hỗ trợ đọc ảnh, dùng giao thức OpenAI (OpenAI, hoặc vLLM/Ollama local)

### 2. Cài đặt (một lần)

```bash
cd backend && pip install -e ".[dev,tracing,kho]" && cd ..   # tracing: Langfuse · kho: Qdrant + PDF/Word (tùy chọn)
cd frontend && npm install && cd ..
```

Tạo file `backend/.env` (xem `backend/.env.example`). **Chuyển từ bản cũ:** file `.env` ở thư mục gốc
giờ phải nằm trong `backend/`.

```ini
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4.1-mini          # model phải đọc được ảnh nếu muốn gửi ảnh đề
# OPENAI_BASE_URL=http://localhost:8001/v1   # nếu dùng model local
```

### 3. Chạy ứng dụng web

Mở **hai terminal**:

```bash
# Terminal 1 — API ở http://localhost:8000
cd backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — giao diện ở http://localhost:3000
cd frontend
npm run dev
```

Mở http://localhost:3000 → gõ đề, hoặc gửi ảnh đề (bấm chọn, kéo-thả, hay dán Ctrl+V).
Trang **Luyện đề** (http://localhost:3000/exam) sinh đề thi vào 10 theo cấu trúc từng tỉnh
hoặc tự chọn chuyên đề, có đồng hồ, chấm ngay khi nộp — không cần API key.

### 4. Các cách chạy khác

Các lệnh Python chạy trong thư mục `backend/`:

| Việc | Lệnh |
|---|---|
| Chạy test (không cần LLM) | `pytest -q` |
| Giải một bài trên dòng lệnh | `python tools/solve.py "Giải phương trình x^2 - 5x + 6 = 0."` |
| Chạy eval (bộ smoke) | `python evals/run.py --set smoke` |
| Xem lại báo cáo eval | `python evals/run.py --report evals/reports/<file>.json` |
| Kiểm tra kiểu frontend | `cd frontend && npm run typecheck` |

Máy có `make` (Linux/macOS/Git Bash) dùng được lối tắt từ thư mục gốc: `make install`, `make test`,
`make api`, `make web-install`, `make web`, `make ui`, `make eval`.

### 5. Lỗi hay gặp trên Windows

| Hiện tượng | Nguyên nhân · cách xử lý |
|---|---|
| `make` is not recognized | PowerShell không có `make` → gõ thẳng lệnh trong bảng trên |
| `&&` báo lỗi cú pháp | PowerShell 5.1 không có `&&` → dùng `;` hoặc gõ từng lệnh |
| `python-multipart not installed` dù đã cài | Lệnh `uvicorn` trỏ tới **Python khác** (vd. 3.11) → luôn chạy `python -m uvicorn ...` |
| `WinError 10013` khi khởi động API | Cổng 8000 đang bị tiến trình cũ giữ → tắt terminal API cũ, hoặc đổi `--port 8001` và đặt `NEXT_PUBLIC_API_URL=http://localhost:8001` cho web |
| Web báo không kết nối được API | Chưa chạy terminal 1, hoặc API lỗi khi khởi động — xem log ở terminal đó |

### 6. Đăng nhập và lịch sử (Supabase)

Mọi trang giải bài / luyện đề / lịch sử **bắt buộc đăng nhập** (tên đăng nhập + mật khẩu, không cần email).
**Không có tự đăng ký**: một tài khoản **admin duy nhất** tạo tài khoản cho học sinh.

1. Supabase → **Connect** → **Session pooler** → chép chuỗi kết nối, thay `[YOUR-PASSWORD]`, dán vào `backend/.env`:
   `DATABASE_URL=postgresql://postgres.<ref>:<mật khẩu>@aws-0-<vùng>.pooler.supabase.com:5432/postgres`
   (không dùng "Direct connection" — gói miễn phí chỉ có IPv6). Bảng tự tạo khi API khởi động.
2. Chưa có `DATABASE_URL` thì API dùng SQLite `backend/data/app.db` — chỉ để phát triển.
3. `SOLVE_DAILY_LIMIT` (mặc định 30): số bài mỗi học sinh được giải mỗi ngày.
4. Tạo admin (một lần, trong `backend/`): `python tools/create_admin.py` — in mật khẩu tạm; lần đầu đăng nhập phải đổi.
   Quên mật khẩu admin: `python tools/create_admin.py --reset`.
5. Admin vào **Quản trị → Học sinh**: dán danh sách họ tên (mỗi dòng một em) → tạo tài khoản, mật khẩu tự
   sinh, bấm **In danh sách** để phát. Học sinh phải đổi mật khẩu ở lần đăng nhập đầu. Quên mật khẩu /
   khóa tài khoản: cũng ở đây.

**Hỏi thêm sau khi giải:** dưới lời giải có ô "Hỏi thêm về bài này" — trợ lý trả lời thẳng dựa trên
đúng lời giải đó, nhắc "[bước a2]" thì bước đó được tô sáng trên hình, dẫn chứng định lí tới cấp chương
SGK. Câu trả lời KHÔNG qua Verifier như lời giải chính (giao diện ghi rõ). Giới hạn `CHAT_PER_SOLVE_LIMIT`
câu/bài, `CHAT_DAILY_LIMIT` câu/ngày. Hỏi đáp lưu cùng bài trong Lịch sử.

Lịch sử lưu: mỗi lượt giải (đề, ảnh đề, lời giải, gợi ý, hình — mở lại không tốn lượt gọi model) và mỗi
đề luyện (bài làm, điểm, điểm tự chấm). Mỗi học sinh chỉ xem được lịch sử của mình.

### 7. Kho đề Qdrant — thêm đề mỗi ngày

1. Đặt trong `backend/.env`: `QDRANT_URL` + `QDRANT_API_KEY` (Qdrant Cloud), hoặc tạm `QDRANT_PATH=data/qdrant`
   (lưu cục bộ).
2. Đưa kho có sẵn lên Qdrant (một lần; tắt API trước nếu dùng kho cục bộ):
   `python tools/index_bank.py`
3. Đăng nhập tài khoản admin → **Quản trị → Kho đề** → kéo-thả PDF / Word / ảnh đề (nên kèm đáp án) → sửa và
   duyệt từng bài. Chỉ bài đã duyệt mới vào đề luyện và gợi ý bài tương tự.
4. Chuyển kho (vd cục bộ → Cloud): đổi `.env`, rồi `python tools/index_bank.py --uploads` để ghi lại cả
   bài tải lên đã duyệt.

Máy ít RAM (dưới 8 GB) mà `npm run dev` bị "heap out of memory": chạy bản build
`npm run build && npm run start` — nhẹ hơn nhiều.

Biến môi trường thêm: `RAG_REQUIRE_REVIEWED=1` (production — chỉ nạp sổ tay đã soát),
`CORS_ORIGINS` (mặc định `http://localhost:3000`).

### 8. Deploy (frontend và backend riêng)

**Backend** (Render / Railway / Fly.io — có sẵn `backend/Dockerfile`):

1. Tạo dịch vụ Docker, Root Directory = `backend`. Container đọc biến `PORT` của nền tảng.
2. Đặt biến môi trường như `backend/.env.example`: `OPENAI_API_KEY`, `MODEL_NAME`, `DATABASE_URL`
   (Supabase — **bắt buộc** khi deploy, ổ đĩa container mất khi khởi động lại), `QDRANT_URL` +
   `QDRANT_API_KEY`, `COOKIE_SECURE=1`, `RAG_REQUIRE_REVIEWED=1`, `CORS_ORIGINS=<domain frontend>`.
3. Kiểm tra: `https://<backend>/api/health`. Tạo admin một lần: chạy `python tools/create_admin.py`
   ở máy mình với cùng `DATABASE_URL`.

**Frontend** (Vercel):

1. Import repo, **Root Directory = `frontend`** (Next.js tự nhận).
2. Biến môi trường (cách khuyên dùng — đi qua proxy, cookie đăng nhập cùng tên miền):
   `BACKEND_URL=https://<backend>` và `NEXT_PUBLIC_API_URL=` (để **rỗng**).
   Trình duyệt gọi `/api/*` trên domain của frontend, Next.js chuyển tiếp sang backend.
3. Cách khác — gọi thẳng backend: `NEXT_PUBLIC_API_URL=https://<backend>` và ở backend đặt thêm
   `COOKIE_SAMESITE=none`. Safari chặn cookie bên thứ ba nên đăng nhập có thể hỏng — ưu tiên cách ở bước 2.

Ảnh đề học sinh gửi (`data/uploads`, `data/user_images`) lưu trên đĩa container: gắn volume
(Render Disk / Railway Volume) vào `/app/data/uploads` và `/app/data/user_images` nếu muốn giữ lâu dài.

## Bốn nguyên tắc kiến trúc

**1. Đồ thị cố định, không ủy quyền động.**
Toán lớp 9 là miền đóng, quy trình xử lý luôn giống nhau. Không agent nào tự
quyết gọi agent khác. Debug được, đo được, chi phí dự đoán được.

**2. LLM không bao giờ sinh tọa độ.**
LLM sinh *kịch bản dựng hình* khai báo (`packages/geometry/dsl.py`); engine
thực thi bằng công thức toán học nên quan hệ hình học đúng ở độ chính xác máy.
Đây là chỗ đa số dự án tương tự thất bại.

**3. Kiểm chứng bằng code, không bằng LLM.**
Nếu để một LLM kiểm tra lời giải của LLM khác, hai bên sẽ sai giống nhau. Giá
trị nằm ở chỗ dùng cơ chế hoàn toàn khác: SymPy giải lại độc lập, engine hình
học dựng lại 5 cấu hình ngẫu nhiên và kiểm tra vị từ bằng số.

**4. Thà thừa nhận không chắc còn hơn trả lời sai.**
Vòng lặp Solver ↔ Verifier giới hạn cứng 2 lần. Sau đó trả về phần đã chắc
chắn kèm nhãn `confidence`, không cố nữa.

## Luồng xử lý

```
Parser → Router → { Solver ∥ Draftsman } → Verifier → [Critic] → Render → Pedagogue
                        ↑                       │
                        └──── giải lại (tối đa 2) ┘
```

Solver và Draftsman chạy **song song** — cả hai chỉ cần đề đã chuẩn hóa,
tiết kiệm khoảng 40% độ trễ. Verifier đối chiếu chéo hai đầu ra: nếu lời giải
nhắc điểm K mà kịch bản dựng hình không có K, một trong hai đã hiểu sai đề.

## Thang leo thang theo độ khó

| Mức | Chiến lược | Độ trễ mục tiêu | Lưu lượng dự kiến |
|---|---|---|---|
| 1 quen thuộc | Một lượt gọi, verify | < 12s | ~75% |
| 2 khó vừa | Nạp sổ tay phương pháp, sinh 3 lời giải, Verifier chọn | < 35s | ~20% |
| 3 rất khó | Hai pha: giải tự do → dò bổ đề → hạ về công cụ lớp 9 | < 90s | ~5% |

### Kỹ thuật hai pha (mức 3)

1. **Giải tự do** — cho phép mọi công cụ (tọa độ, lượng giác, phương tích).
   Mục tiêu duy nhất: tìm ra đáp án và đường đi.
2. **Dò bổ đề** — `verifier/lemma_finder.py` quét tự động tập vị từ trên hình
   đã dựng. Mệnh đề đúng trên cả 5 cấu hình ngẫu nhiên là bổ đề thật.
3. **Hạ cấp** — Solver chứng minh lại bằng `allowed_tools`, dùng bổ đề làm mốc.
   Bài khó bị bẻ thành chuỗi bài dễ.

Phần khó nhất của một bài hình là *đoán được cần chứng minh gì*, chứ không
phải chứng minh nó. Bước 2 giải quyết đúng phần đó.

## Vì sao không đưa nguyên SGK vào RAG

SGK viết theo mạch dạy học, nên retrieval theo độ tương đồng sẽ trả về đoạn
dẫn nhập hoặc ví dụ dễ hơn nhiều — vài nghìn token gần đúng nhưng không dùng
được, lại làm loãng chỉ dẫn quan trọng khác trong prompt.

Model cũng **không thiếu kiến thức đó**. Nó đã biết định lý góc nội tiếp. Cái
nó thiếu là *ràng buộc*, và ràng buộc phải là dữ liệu có cấu trúc để code kiểm
tra được, không phải văn xuôi để model đọc.

| Trích từ SGK | Định dạng | Vào đâu |
|---|---|---|
| Định lý, công thức, ký hiệu từng chương | `data/curriculum/*.yaml` | Guardrail — **không qua vector search** |
| Thứ tự chương, điều kiện tiên quyết | `data/curriculum/*.yaml` | Router |
| 2–3 lời giải mẫu mỗi chuyên đề | `data/problems/` | RAG few-shot |

Vector search **chỉ** chứa hai loại tài liệu, cả hai đều không có trong SGK:

- **Sổ tay phương pháp** (`data/methods/`) — tổ chức theo *mục tiêu chứng minh*,
  không theo chương. Truy xuất bằng `goal_type`. Bạn không tìm "bài giống",
  bạn tìm "chiến lược phù hợp". Đây là thứ giúp giải bài khó và là khoản đầu
  tư có giá trị cao nhất của dự án (~40–60 tài liệu, giáo viên soạn 3–4 tuần).
- **Bài giải mẫu đề thi vào 10** — đúng mức độ khó học sinh thực sự gặp. Bài
  tập SGK dễ hơn một bậc rõ rệt; dùng làm few-shot sẽ khiến model bắt chước
  nhầm mức độ.

**Ngoại lệ:** khi học sinh hỏi *kiến thức* ("cho em xem lại định nghĩa tứ giác
nội tiếp") thì trích đúng đoạn SGK là câu trả lời tốt nhất. Nhưng đó là tính
năng khác, collection riêng, Router phải phân biệt được — đừng trộn chung.

## Router phân loại thế nào

Phân loại dạng toán **không phải việc tra cứu tài liệu**. Prompt của Router
chỉ cần *danh mục nhãn* (`CurriculumMap.label_catalog()`, khoảng 600 token),
không cần nội dung sách — ngắn hơn ba cuốn SGK khoảng 600 lần và chính xác hơn,
vì nó cho model một tập lựa chọn đóng.

**`goal_type` mới là thứ quan trọng.** Chuyên đề cho biết *được dùng công cụ gì*;
`goal_type` cho biết *nên đi hướng nào*, và nó là khóa truy xuất sổ tay phương
pháp. Hai bài cùng GEO-9 nhưng một bài chứng minh nội tiếp, một bài tìm điểm
cố định, cần hai bộ chiến lược khác hẳn.

Router phải **tách theo từng ý** (a, b, c...) — nếu gán cả bài một nhãn theo ý
khó nhất, bạn sẽ chạy chiến lược mức 3 tốn kém cho cả những ý đơn giản.

**Lộ trình:** LLM nhỏ ở Sprint 2 → fine-tune PhoBERT sau ~2000 lượt thật
(nhanh hơn 30 lần, chính xác hơn trên miền dữ liệu của bạn). Đừng vội fine-tune:
chạy bằng LLM trước để thu dữ liệu gán nhãn miễn phí.

## Chọn model

Chiến lược **hybrid, tách theo vai trò** — xem `packages/core/math9_core/llm/client.py`,
bảng `MODEL_POLICY`. Sửa ở đó, không rải rác trong agent.

| Vai trò | Model | Lý do |
|---|---|---|
| Router | Classifier fine-tune (PhoBERT) | Nhanh gấp 10, rẻ gấp 100 |
| Draftsman | Qwen3-14B/32B local + LoRA | Sinh JSON có cấu trúc — model nhỏ làm tốt sau fine-tune |
| Solver mức 1 | Qwen3-32B local | 75% lưu lượng, gần như miễn phí biên |
| Solver mức 2–3 | API model mạnh | Hình khó — chỗ chênh lệch năng lực lộ rõ nhất |
| Pedagogue | Qwen3-8B local | Diễn đạt lại, không cần suy luận |

**Đừng dùng model tiếng Việt chuyên biệt cho Solver.** PhoGPT, VinaLLaMA được
tối ưu cho văn phong tiếng Việt, không phải suy luận toán — bạn sẽ nhận lời
giải trôi chảy nhưng sai toán, kiểu sai nguy hiểm nhất. Tiếng Việt ở đây chủ
yếu là *đầu ra trình bày*, vá được bằng few-shot; năng lực suy luận thì không.

**Cảnh báo về benchmark:** điểm MATH-500 hay AIME cao không dự đoán được năng
lực bạn cần. Các benchmark đó chủ yếu là bài *tính ra một số*; bài của bạn phần
lớn là *chứng minh*. Và không benchmark nào đo được "có tuân thủ ràng buộc chỉ
dùng công cụ lớp 9 không". Câu trả lời thật nằm ở con số bạn tự đo trên
`data/eval/core.jsonl`.

## Bắt đầu từ đâu

**Đừng viết code trong tuần đầu.** Thứ tự đúng:

1. **Tìm giáo viên Toán THCS** (≥10 giờ/tuần) — đường găng dài nhất, làm ngay.
2. Gom 30 bài từ đề thi vào 10 công khai (10 đại số quen thuộc, 10 hình cơ bản,
   7 hình câu cuối, 3 thống kê–xác suất).
3. Chạy thủ công qua một model API mạnh, prompt tối giản, không RAG không guardrail.
4. Giáo viên chấm theo 5 trục: đáp án / lập luận / chương trình / trình bày / hình vẽ.
5. Tổng hợp một trang: bao nhiêu phần trăm sai ở mỗi trục, sai kiểu gì.

Bảng đó quyết định thứ tự sprint. Kết quả sẽ khác dự đoán của bạn ở ít nhất
một trục — đó chính là lý do phải làm trước.

## Lộ trình

| Sprint | Mục tiêu |
|---|---|
| 0 | Bộ eval 200 bài, đo baseline. **Chưa viết sản phẩm.** |
| 1 | Bản đồ chương trình 17 chuyên đề + guardrail. Sổ tay phương pháp bắt đầu **từ đây**, không để cuối |
| 2–3 | MVP đại số: chat + KaTeX + Solver + Verifier SymPy |
| 4–5 | Engine hình học (đã có scaffold) — hoàn thiện DSL, layout, render |
| 6–7 | Hình học end-to-end: Draftsman, Verifier hình, hình đồng bộ bước giải |
| 8 | 40+ tài liệu sổ tay, RAG theo `goal_type`, đo lại bộ hard |
| 9 | Thang leo thang, kỹ thuật hai pha, dò bổ đề |
| 10 | Chế độ gợi ý từng bước (Pedagogue) |
| 11 | Đầu vào ảnh (Parser OCR/VLM) |
| 12 | Định tuyến model theo độ khó, cache, giảm chi phí |

## Cấu trúc thư mục

```
backend/
  api/           FastAPI + SSE (điểm vào: api/main.py)
  packages/
    geometry/    DSL, engine dựng hình, ràng buộc số, layout, render SVG
    verifier/    vị từ, kiểm chứng hình học, SymPy, dò bổ đề
    curriculum/  schema, loader YAML, guardrail 2 lớp, retrieval BM25
    core/        ProblemState, orchestrator, agent, chính sách model
    ingest/      crawl, trích xuất, chuẩn hóa, tách bài, khử trùng lặp
    methods/     tái tổ chức tài liệu tra cứu thành sổ tay theo goal_type
    retrieval/   RAG: hybrid search, 3 collection tách biệt, cổng chặn draft
    exam/        luyện đề: kho bài thật, biến thể đổi số, cấu trúc đề theo tỉnh, chấm
    accounts/    tài khoản, phiên đăng nhập, lịch sử
  data/
    curriculum/  bản đồ chương trình YAML — KHÔNG qua vector search
    methods/     sổ tay phương pháp theo goal_type — RAG
    problems/    bài giải mẫu — RAG few-shot
    eval/        bộ đánh giá 4 tầng (đồng thời là kho bài thật cho luyện đề)
    exam/        cấu trúc đề thi vào 10 theo tỉnh (blueprints.yaml)
  prompts/       template Router, Solver, Draftsman
  evals/         runner + graders (chấm đáp án bằng SymPy, chấm hình bằng verifier)
  tools/         dòng lệnh: giải bài, soạn bài mẫu, crawl, hàng đợi soát
  tests/         test không cần LLM (LLM được giả lập)
  Dockerfile     image deploy backend
frontend/        Next.js: nhập đề/ảnh, tiến trình, gợi ý, lời giải, hình tô sáng
  e2e/           kiểm tra giao diện bằng trình duyệt headless
docs/            tài liệu thiết kế, công việc
```

## Rủi ro cần theo dõi

| Rủi ro | Cách giảm thiểu |
|---|---|
| Trả lời sai một cách tự tin | Verifier bằng code; nhãn `confidence`; giới hạn vòng lặp |
| Hình vẽ sai quan hệ | LLM không sinh tọa độ; kiểm chứng vị từ trên 5 cấu hình |
| Học sinh chép bài, giáo viên phản đối | Chế độ gợi ý là mặc định; làm việc với trường từ sớm |
| Chi phí token vượt doanh thu | `MODEL_POLICY` định tuyến theo độ khó; cache |
| Bản quyền SGK | Dùng đề thi công khai; tự soạn lời giải; không số hóa nguyên văn |
| Sổ tay phương pháp chậm | Bắt đầu Sprint 1, song song với kỹ thuật |

## Tài liệu công việc

Xem thư mục [`docs/`](docs/README.md) — mô tả chi tiết công việc theo package, sprint, vai trò. Bắt đầu từ `docs/00-tong-quan.md`.
