# Nền tảng RAG

## RAG là gì?

RAG là Retrieval-Augmented Generation: mô hình trả lời không chỉ dựa vào kiến thức có sẵn của LLM, mà trước hết truy xuất tài liệu liên quan rồi dùng tài liệu đó để sinh câu trả lời.

## Vì sao cần RAG?

LLM có thể trả lời sai khi thiếu ngữ cảnh hoặc gặp dữ liệu không nằm trong kiến thức huấn luyện. RAG giúp:

- Đưa nguồn dữ liệu cụ thể vào câu trả lời.
- Giảm hallucination.
- Cho phép kiểm tra lại bằng source chunks.
- Dễ cập nhật tri thức hơn fine-tuning.

## Pipeline RAG trong dự án này

1. Load dataset `sailor2/Vietnamese_RAG`, config `BKAI_RAG`.
2. Join context tiếng Việt thành text sạch.
3. Chia text bằng 4 chiến lược chunking.
4. Embed chunks bằng Gemini embedding.
5. Lưu vector vào ChromaDB, mỗi strategy có một collection riêng.
6. Khi người dùng hỏi, embed question bằng cùng provider.
7. Query collection tương ứng với strategy đã chọn.
8. Lấy top-k chunks làm context.
9. Gemini Flash sinh answer dựa trên question + retrieved context.
10. UI/CLI hiển thị answer và source chunks.
