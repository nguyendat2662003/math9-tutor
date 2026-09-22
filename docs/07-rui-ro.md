# 07 — Rủi ro

Xếp theo mức độ nghiêm trọng. Cột "đã xử lý" đánh dấu phần scaffold đã có cơ chế
giảm thiểu.

| Rủi ro | Mức | Cách giảm thiểu | Đã xử lý |
|---|---|---|---|
| Trả lời sai một cách tự tin | Cao | Verifier bằng code; nhãn confidence; giới hạn vòng lặp 2 | ✅ |
| Hình vẽ sai quan hệ | Cao | LLM không sinh tọa độ; kiểm chứng vị từ 5 cấu hình | ✅ |
| Học sinh chép bài, giáo viên phản đối | Cao | Chế độ gợi ý mặc định; làm việc với trường sớm | 🔲 UI |
| Chi phí token vượt doanh thu | TB | Định tuyến model theo độ khó; cache | ⚙️ chính sách |
| Bản quyền SGK/tài liệu | TB | Đề công khai; tự soạn; không số hóa nguyên văn | ✅ ranh giới |
| Sổ tay chậm tiến độ | TB | Bắt đầu Sprint 1; pipeline rút từ tài liệu có sẵn | ✅ pipeline |
| Router phân loại sai | TB | Trả top-2; hybrid RAG cứu vãn; Verifier là lưới an toàn | ✅ |
| Trích công thức PDF hỏng | TB | Chấm chất lượng, định tuyến OCR, hàng đợi soát | ✅ |
| Đề thi thay đổi theo năm | Thấp | Bản đồ chương trình tách khỏi code | ✅ |
| Bộ sách khác nhau (3 bộ) | Thấp | Chốt bộ chuẩn trước; YAML tách theo bộ nếu cần | 🔲 chốt |

## Ba rủi ro cần chú ý nhất

**Sai mà tự tin.** Đây là lỗi phá hủy niềm tin nhanh nhất. Kiến trúc đã chống
bằng Verifier độc lập — nhưng phải giữ kỷ luật: không bao giờ hiển thị lời giải
chưa qua kiểm chứng như thể chắc chắn.

**Học sinh chép bài.** Không phải rủi ro kỹ thuật mà là rủi ro thị trường. Một
chatbot giải sẵn bài tập sẽ bị phụ huynh và giáo viên phản đối, và thực tế làm
học sinh học kém đi. Chế độ mặc định phải là gợi ý từng bước kiểu Socratic.
Cần làm việc với trường từ sớm để hiểu ranh giới chấp nhận được.

**Đường găng nội dung.** Không phải code chậm mà là sổ tay giáo viên chậm. Xem
`03` và `04`. Giảm thiểu bằng cách bắt đầu ngay ngày 1 và dùng pipeline tái tổ
chức thay vì soạn tay.
