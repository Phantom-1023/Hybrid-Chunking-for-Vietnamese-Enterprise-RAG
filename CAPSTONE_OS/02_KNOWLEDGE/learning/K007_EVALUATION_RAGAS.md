# Đánh giá bằng RAGAS

## RAGAS là gì?

RAGAS là framework đánh giá hệ thống RAG bằng các metric định lượng. Nó kiểm tra cả chất lượng câu trả lời và chất lượng context được truy xuất.

## Faithfulness

Faithfulness đo xem câu trả lời có bám vào context được truy xuất hay không. Metric này giúp phát hiện hallucination.

## Answer Relevancy

Answer Relevancy đo mức độ câu trả lời liên quan trực tiếp đến câu hỏi. Trả lời dài nhưng lệch ý sẽ bị điểm thấp.

## Context Recall

Context Recall đo xem retrieved context có bao phủ đủ thông tin cần thiết từ ground truth hay không.

## Context Precision

Context Precision đo xem các context được truy xuất có thật sự hữu ích hay chứa nhiều nhiễu.

## Vì sao dùng RAGAS?

Dự án cần bằng chứng khoa học để so sánh 4 chiến lược chunking. RAGAS cho phép biến demo RAG từ "chạy được" thành "đánh giá được". Trạng thái hiện tại: RAGAS chưa hoàn thành, chưa được phép fake kết quả.
