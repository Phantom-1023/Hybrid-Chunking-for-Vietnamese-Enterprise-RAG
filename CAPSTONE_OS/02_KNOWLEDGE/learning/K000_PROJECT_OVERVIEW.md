# Tổng quan dự án

## Dự án làm gì?

Dự án xây dựng demo RAG cho dữ liệu tiếng Việt, tập trung so sánh 4 chiến lược chunking trên dataset public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`.

Mục tiêu không phải tạo chatbot doanh nghiệp hoàn chỉnh ngay, mà là chứng minh pipeline RAG chạy được và có thể đánh giá chiến lược chunking bằng số liệu.

## Research question

Với dữ liệu tiếng Việt, chiến lược chunking nào giúp RAG truy xuất đúng ngữ cảnh và trả lời tốt hơn: fixed, recursive, semantic hay paragraph?

## Current MVP status

- Verify dataset: đã chạy.
- Index ChromaDB: đã có 4 collection.
- CLI query: đã chạy.
- Streamlit demo: đã chạy.
- Demo với record thật từ dataset public: đã chạy.
- Execution patch: đang dùng `gemini-embedding-001` vì API key hiện tại không hỗ trợ `text-embedding-004`.

## Demo hiện tại chứng minh gì?

- Dataset public load được.
- 4 chiến lược chunking đều tạo chunk.
- Chunks đã được lưu vào ChromaDB theo từng collection.
- Người dùng chọn strategy, hỏi câu hỏi và nhận answer + source chunks.
- UI có thể chọn record thật từ dataset, không chỉ câu hỏi khóa cứng.

## Chưa làm xong

- Chưa có RAGAS benchmark chính thức.
- Chưa có `benchmark_results.csv`.
- Chưa có kết luận định lượng chiến lược nào tốt nhất.
- Upload tài liệu doanh nghiệp thật không nằm trong MVP.
- Hybrid search, reranking và GraphRAG là hướng mở rộng, chưa làm.
