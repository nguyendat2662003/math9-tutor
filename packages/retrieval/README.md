# Tầng RAG

Truy xuất chiến lược giải và bài mẫu, nạp vào prompt Solver. Đây là RAG **thật** —
hybrid search có vector, không chỉ BM25.

## Ba collection TÁCH BIỆT

| Collection | Chứa gì | Truy theo | Trả lời câu hỏi |
|---|---|---|---|
| `methods` | Sổ tay phương pháp | **goal_type là chính** | "nên đi hướng nào" |
| `worked_examples` | Bài giải mẫu chi tiết | **độ tương đồng là chính** | "trình bày thế nào" |
| `concepts` | Định nghĩa/kiến thức SGK | độ tương đồng | "định nghĩa X là gì" (câu hỏi lý thuyết) |

Tách vì chúng phục vụ việc khác nhau. Trộn chung thì truy xuất trả về hổ lốn —
đúng cái lỗi khiến nhiều chatbot toán kém.

## Vì sao goal_type là tín hiệu chính cho sổ tay

Hai bài này từ ngữ gần trùng khớp nhưng cần chiến lược khác hẳn:

> ...kẻ hai tiếp tuyến AB, AC. **Chứng minh ABOC nội tiếp.**
> ...kẻ hai tiếp tuyến AB, AC. **Chứng minh MN đi qua điểm cố định.**

Vector search và BM25 xếp chúng cạnh nhau vì mặt chữ giống. Nhưng bài một dùng
"hai góc vuông cùng nhìn một đoạn", bài hai cần "dự đoán điểm cố định". Nạp nhầm
sổ tay còn tệ hơn không nạp gì.

Nên `search_methods` **lọc theo goal_type trước**, chỉ dùng hybrid (BM25+vector
gộp bằng RRF) để xếp hạng trong nhóm cùng goal_type, hoặc cứu vãn khi Router
phân loại sai.

## Hybrid search

`_hybrid` chạy BM25 và vector song song rồi gộp bằng Reciprocal Rank Fusion —
không cần chuẩn hóa điểm giữa hai phương pháp. BM25 bắt khớp từ khóa chính xác
(tên định lý), vector bắt tương đồng ngữ nghĩa (cách diễn đạt khác nhau).

## Embedder đổi được theo giai đoạn

| Backend | Khi nào | Ghi chú |
|---|---|---|
| `HashingEmbedder` | Test, kho nhỏ | Không cần model, offline, tất định |
| `LocalEmbedder` (bge-m3) | Production | Đa ngữ, tiếng Việt tốt, self-host |
| API embedding | Chất lượng cao nhất | Tốn tiền |

**Tránh model chỉ tiếng Anh** — nó embed "tứ giác nội tiếp" rất kém.

## Cổng chặn: chỉ sổ tay đã soát mới vào RAG

`load_methods(require_reviewed=True)` bỏ qua mọi sổ tay `status != reviewed`.
Sổ tay draft thiếu "khi nào không dùng" và "bẫy" — nạp vào có thể đẩy Solver
sai hướng. Đây là bảo hiểm nối tiếp với `gate_for_rag` ở package methods.

## Hai loại lời giải, chỉ một được vào kho mẫu

`load_worked_examples` loại bỏ `solution_type == "answer_key"`. Hướng dẫn chấm
của Sở viết cụt lủn, không nêu căn cứ; nạp làm few-shot sẽ dạy model viết lời
giải không có căn cứ — đúng thứ guardrail đang cố chặn. Chỉ lời giải chi tiết
(`detailed`) mới vào kho mẫu.

## Solver dùng thế nào

Orchestrator gọi `RagService.retrieve` sau Router, đặt kết quả vào
`state.retrieved`. Prompt Solver đọc `{{ method_notes }}` và `{{ worked_examples }}`
từ đó. Bài nhiều ý gom sổ tay của mọi goal_type xuất hiện.

## SGK vẫn KHÔNG ở đây

Collection `concepts` chỉ dùng khi học sinh hỏi **kiến thức** ("định nghĩa tứ
giác nội tiếp"), không phải khi giải bài. Router phải phân biệt hai loại truy
vấn. Kho giải bài (`methods` + `worked`) tuyệt đối không chứa SGK.
