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
