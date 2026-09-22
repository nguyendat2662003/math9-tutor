# 06 — Đánh giá

Không có bộ đánh giá, mọi thay đổi prompt đều là đoán mò. Đây là nền tảng của
toàn dự án, làm từ Sprint 0.

## Bốn tầng eval

| Tệp | Số bài | Nguồn | Chạy khi nào |
|---|---|---|---|
| `smoke.jsonl` | 30 | Trải đều chuyên đề | Mỗi commit |
| `core.jsonl` | 200 | Đề thi vào 10 các Sở | Mỗi PR |
| `hard.jsonl` | 80 | Câu cuối đề thi, HSG | Hàng tuần |
| `figure.jsonl` | 100 | Bài hình có hình chuẩn | Hàng tuần |

## Định dạng một bài

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

Hai trường then chốt:
- **`predicates`** — cho phép chấm hình vẽ TỰ ĐỘNG bằng Verifier. Không chấm
  bằng mắt, không chấm bằng LLM.
- **`topic` + `goal_type`** — do giáo viên gán, để chấm Router TÁCH BẠCH khỏi
  chấm lời giải. Hai lỗi này khác nhau; không tách thì sửa nhầm chỗ.

## Chỉ số và ngưỡng nghiệm thu

| Chỉ số | Cách đo | Ngưỡng |
|---|---|---|
| Độ chính xác đáp án | So khớp SymPy | ≥ 95% (core), ≥ 70% (hard) |
| Hình đúng quan hệ | Verifier hình học | ≥ 98% |
| Vi phạm chương trình | Guardrail | < 2% |
| Độ chính xác Router | So với nhãn giáo viên | ≥ 90% |
| **Sai mà tự tin** | confidence=high nhưng đáp án sai | **< 1%** |
| p50 / p95 độ trễ | Đo trên production | 12s / 60s |

Chỉ số **"sai mà tự tin"** quan trọng nhất — nó đo trực tiếp mức độ đáng tin
của sản phẩm. Trả lời sai một cách tự tin còn tệ hơn thừa nhận không biết.

## Chấm tự động vs chấm người

| Trục | Chấm bằng |
|---|---|
| Đáp án số | SymPy (`evals/graders/answer.py`) |
| Hình vẽ | Verifier + predicates (`evals/graders/figure.py`) |
| Router | So nhãn — tự động |
| Lập luận, trình bày | Giáo viên (mẫu 50 bài/tuần) |

Ba trục đầu tự động hoàn toàn. Chỉ lập luận và trình bày cần người — đó là lý
do cột `predicates` trong eval đáng công điền.

## Công cụ

```bash
python evals/run.py --set smoke                       # mỗi commit, ~4 phút, 3 workers
python evals/run.py --set core --workers 4            # mỗi PR
python evals/run.py --regrade evals/reports/<f>.json  # chấm lại bằng grader mới, không gọi LLM
python evals/run.py --report  evals/reports/<f>.json  # in lại báo cáo
```

Báo cáo JSON gồm `metrics` và `rows` từng bài (đáp án dự đoán, vị từ sai, token,
thời gian) — mở `rows` để xem bài nào sai và vì sao.

## Baseline đầu tiên (2026-09-22, smoke, một model API)

| Chỉ số | Kết quả | Ngưỡng core |
|---|---|---|
| Đáp án đúng | 100% (26/26 chấm được) | ≥ 95% |
| Sai mà tự tin | 0% | < 1% |
| Router topic / goal_type | 96.6% / 89.7% | ≥ 90% |
| Vi phạm chương trình | 0% | < 2% |
| Độ trễ p50 / p95 | 12s / 66s | 12s / 60s |
| Token TB mỗi bài | 5.7k vào / 2.4k ra | — |

Hai bài học từ lần chạy đầu:
- **Grader từng chấm sai 8/30 bài** vì lời giải kèm điều kiện ("với x > 0"), xấp xỉ
  ("≈ 9,93") hay nhắc lại đề ("∛(−27) = −3"). Khi thấy "sai mà tự tin" tăng, đọc
  `rows` trước khi kết luận model sai.
- **81/82 bài trắc nghiệm trong eval không lưu 4 phương án.** Dạng "tính giá trị"
  vẫn chấm được; dạng "khẳng định nào sau đây" bị đánh dấu `data_issue`, không
  chấm. Cần bổ sung phương án vào `statement` khi nhập đề.
