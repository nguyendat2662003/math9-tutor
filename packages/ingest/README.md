# Khâu nhập dữ liệu

```
discover → fetch → extract → normalize → segment → quality → dedupe → xuất JSONL
```

## Crawl cho ra được gì

| Kho | Crawl làm được? |
|---|---|
| Bộ eval (đề + đáp án) | **Có** — mục đích chính |
| Bài giải mẫu cho RAG few-shot | **Có**, sau khi giáo viên soát |
| `data/curriculum/*.yaml` | **Không** — giáo viên chắt từ SGK |
| `data/methods/*.md` | **Không** — không nằm trong tài liệu nào |
| Kịch bản dựng hình | **Không** — Draftsman sinh, Verifier kiểm |

Crawl cho bạn *dữ liệu để đo*, không phải *tri thức để giải*.

## Hai đầu ra, không phải một

- `data/raw/accepted.jsonl` — sạch, dùng được ngay
- `data/raw/review.jsonl` — xếp hàng cho giáo viên soát

Tỉ lệ auto-accept thực tế với PDF đề thi khoảng **50–65%**. Đừng thiết kế quy
trình giả định 100%. Bài hình gần như luôn vào hàng đợi soát vì hình gốc là ảnh
raster, không tái sử dụng được.

## Ba cạm bẫy đã xử lý sẵn

**Dấu phẩy thập phân.** `2,5` phải thành `2.5`, nhưng `(2,0 điểm)` và `x1, x2`
thì không. Xử lý ẩu chỗ này là hỏng toàn bộ dữ liệu số. Xem `normalize.fix_decimal_comma`.

**Công thức vỡ trong PDF.** Font không nhúng cho ra `(cid:97)`, chữ số bị tách
rời. `quality.assess` phát hiện và định tuyến sang OCR thay vì âm thầm chấp nhận.

**Đề đăng lại nhiều nơi.** Cùng một bài với khác số hiệu, khác dấu gạch, khác
watermark. Không lọc thì bộ eval nghiêng nặng về vài bài phổ biến và cho ra
accuracy sai lệch. `dedup` dùng MinHash trên shingle ký tự, bền với khác biệt
định dạng.

## Ranh giới nguồn

Pipeline **từ chối chạy** adapter chưa đặt `verified_public = True`. Checklist
trong `adapters/README.md`.

- **An toàn**: đề tuyển sinh 10 trên cổng thông tin Sở GD&ĐT, đề công khai không cần đăng nhập
- **Tránh**: bản scan SGK/SBT, site có tường phí hoặc yêu cầu tài khoản

Fetcher tôn trọng `robots.txt`, giới hạn 1 request / 2 giây mỗi domain, cache
theo hash URL nên chạy lại không tải lại.

## Quy trình với giáo viên

```bash
python tools/crawl.py --source <tên> --dry-run   # kiểm tra link trước
python tools/crawl.py --source <tên>             # tải và xử lý
python tools/review_queue.py export              # xuất CSV mở bằng Excel
# giáo viên điền: statement_fixed, topic, goal_type, difficulty, answer, predicates
python tools/review_queue.py import --src review_done.csv
```

Cột `predicates` là cột quan trọng nhất — nó cho phép chấm hình vẽ **tự động**
bằng Verifier, không cần chấm bằng mắt. Định dạng:
`[{"kind":"concyclic","args":["A","B","O","C"]}]`

## Ưu tiên định dạng nguồn

DOCX > HTML có MathJax > PDF text > PDF scan.

DOCX giữ công thức trong OMML nên trích tốt hơn PDF nhiều. Nếu một nguồn có cả
hai định dạng, luôn lấy DOCX.
