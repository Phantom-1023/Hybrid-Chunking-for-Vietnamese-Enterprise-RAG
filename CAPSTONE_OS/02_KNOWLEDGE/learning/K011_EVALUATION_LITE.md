# Evaluation-lite

## Evaluation-lite là gì?

Evaluation-lite là cách đánh giá nhỏ, chạy nhanh, dùng các tín hiệu đo được trực tiếp từ pipeline hiện tại. Nó giúp nhóm có benchmark thật ban đầu mà không phải chạy full RAGAS tốn quota hoặc phụ thuộc nhiều thư viện.

## Nó khác RAGAS thế nào?

RAGAS là framework đánh giá RAG chuẩn hơn, có các metric như Faithfulness, Answer Relevancy, Context Recall và Context Precision. Evaluation-lite không thay thế RAGAS và không được claim là RAGAS. Nó chỉ là benchmark proxy để chứng minh hệ thống có thể đo lường retrieval/generation thật.

## Dự án dùng metric nào?

- `top1_hit_rate`: chunk đầu tiên có cùng `record_id` với câu hỏi hay không.
- `topk_hit_rate`: trong top-k chunks có chunk nào cùng `record_id` hay không.
- `avg_distance`: khoảng cách trung bình ChromaDB trả về cho retrieved chunks.
- `answer_keyword_overlap`: độ trùng keyword đơn giản giữa output đánh giá và ground truth. Mặc định C-012 dùng retrieved source chunks làm retrieval-only output để tránh tốn quota LLM; nếu bật `EVAL_USE_LLM_GENERATION=true` thì metric này dùng answer do LLM sinh.
- `avg_score`: điểm tổng hợp chuẩn hóa từ các metric lite.

## Vì sao chưa chạy full RAGAS?

Full RAGAS có thể chậm, phụ thuộc thêm package/model và tốn quota API. MVP hiện ưu tiên có benchmark nhỏ, thật, không fake số liệu. Khi ổn định quota và dependency, nhóm sẽ chạy RAGAS chính thức để thay thế hoặc bổ sung evaluation-lite.

## Nếu thầy hỏi thì trả lời gì?

Trả lời ngắn: "Hiện nhóm đã có evaluation-lite để so sánh 4 chiến lược chunking bằng tín hiệu thật từ retrieval và generation. Đây chưa phải RAGAS. Nhóm không dùng số liệu giả; full RAGAS là bước tiếp theo để có đánh giá học thuật đầy đủ hơn."
