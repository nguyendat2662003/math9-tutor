# Bộ đánh giá

**Đây là thứ phải làm TRƯỚC KHI viết sản phẩm.** Không có bộ eval, mọi thay
đổi prompt sau này đều là đoán mò.

## Bốn tầng

| Tệp | Số bài | Nguồn | Chạy khi nào |
|---|---|---|---|
| `smoke.jsonl` | 30 | Trải đều chuyên đề | Mỗi commit |
| `core.jsonl` | 200 | Đề thi vào 10 các Sở | Mỗi PR |
| `hard.jsonl` | 80 | Câu cuối đề thi, đề HSG | Hàng tuần |
| `figure.jsonl` | 100 | Bài hình có hình chuẩn | Hàng tuần |
| `golden.jsonl` | 153 | Bài có đáp án ĐÃ KIỂM CHỨNG độc lập (xem dưới) | Khi chọn / đổi model |

## Định dạng

```json
{
  "id": "hn-2024-c4a",
  "source": "Tuyển sinh 10 Hà Nội 2024, câu 4a",
  "statement": "Cho đường tròn (O) và điểm A nằm ngoài...",
  "mode": "exam10",
  "gold": {
    "topic": "GEO-9",
    "goal_type": "prove_concyclic",
    "difficulty": 1,
    "answer": null,
    "predicates": [{"kind": "concyclic", "args": ["A","B","O","C"]}]
  },
  "teacher_notes": "Bẫy: phải nêu rõ hai góc vuông trước khi kết luận"
}
```

Trường `predicates` cho phép chấm hình vẽ **tự động** — engine dựng lại hình
rồi kiểm tra bằng số. Không chấm bằng mắt, không chấm bằng LLM.

Trường `topic` và `goal_type` do giáo viên gán, dùng để chấm Router **tách bạch**
khỏi chấm lời giải. Hai lỗi này rất khác nhau; không tách ra đo riêng thì sẽ
sửa nhầm chỗ.

## Chỉ số và ngưỡng

| Chỉ số | Ngưỡng |
|---|---|
| Độ chính xác đáp án | ≥ 95% (core), ≥ 70% (hard) |
| Hình đúng quan hệ | ≥ 98% |
| Vi phạm chương trình | < 2% |
| Độ chính xác Router | ≥ 90% |
| **Sai mà tự tin** | **< 1%** |

Chỉ số cuối quan trọng nhất — nó đo trực tiếp mức độ đáng tin của sản phẩm.


## Bộ golden (`golden.jsonl`)

Dùng để so sánh model (vd. `gpt-6-luna` với `gpt-5.6-luna`) khi không muốn số liệu bị nhiễu bởi **đáp án gốc sai**.
Các bộ `core`/`hard` lấy đáp án từ nhiều nguồn (216/275 dòng là `ben_thu_ba` — bài giải trên mạng), không ai
đối chiếu lại; ở golden mỗi đáp án đã được giải lại độc lập.

| Bậc | Số bài | Nguồn đáp án | Kiểm chứng |
|---|---|---|---|
| **A** | 24 | Hướng dẫn chấm chính thức của Sở GD&ĐT (`hdc_so`) | Giải lại bằng tay + SymPy/số, đều khớp |
| **B** | 129 | Bên thứ ba (`ben_thu_ba`) | Giải lại độc lập bằng tay + SymPy/số, đều khớp |

Cách kiểm chứng KHÔNG dùng kết quả của model đang được đánh giá để chọn bài (chọn theo mức khớp của model sẽ làm
điểm cao giả). Bài loại ra, kèm lý do, ở `golden_excluded.json` (đề thiếu dữ kiện, thiếu phương án, chứng minh
không có giá trị cuối...). Đã loại sẵn bài cần hình bắt buộc, bài đề OCR cần soát, bài lời giải vượt chương trình.

**Chưa có giáo viên ký duyệt.** Việc "giải lại độc lập" do AI làm (tính tay + SymPy/số). Bậc A có thêm nguồn chính thức
nên đáng tin hơn; số liệu quyết định (chọn model, đổi prompt) nên đọc theo bậc A trước. Giáo viên nên soát bậc B,
đặc biệt các bài khó (độ khó 3).

Khác các bộ khác, mỗi dòng golden có:
- `verification`: `{tier, by, checked}`.
- `grading: "context"`: đáp án gốc phải nằm TRỌN trong câu trả lời, số thừa chỉ được là số đã có trong đề
  (cứu các câu đúng mà model nhắc lại đề như "Có 14 xe 7 chỗ"). Số thừa không có trong đề thì vẫn bị chấm sai.
- `gold.accept` (tùy chọn): cách viết khác được chấp nhận (vd. `32π/3` và `33,51`).
- `gold.note`: đáp án gốc đầy đủ khi đã rút gọn về giá trị cần so.

**Giới hạn**: golden chỉ gồm bài có GIÁ TRỊ CUỐI để so (số, biểu thức, phương án, Đúng/Sai). Bài chứng minh hình thuần
túy không nằm trong golden — dùng `figure.jsonl` (chấm bằng Verifier). Chuyên đề GEO-9 vì vậy chỉ có 10 bài.

```bash
python evals/run.py --set golden --model gpt-6-luna --workers 2
python evals/run.py --regrade evals/reports/golden_<model>.json   # chấm lại sau khi sửa bộ chấm, không gọi model
pytest tests/test_golden_dataset.py                               # giữ bộ dữ liệu sạch
```
