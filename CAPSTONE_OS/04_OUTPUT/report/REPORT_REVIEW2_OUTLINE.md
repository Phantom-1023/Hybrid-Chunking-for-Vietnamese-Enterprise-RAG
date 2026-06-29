# Khung báo cáo Review 2

Tài liệu này là khung chuẩn bị report, chưa phải báo cáo cuối. Không được tự điền số benchmark khi chưa có kết quả RAGAS thật.

## Cấu trúc báo cáo đề xuất

| Chương | Nội dung cần có | Artifact hỗ trợ | Trạng thái |
|---|---|---|---|
| 1. Giới thiệu | Bối cảnh quản lý tri thức tiếng Việt, vấn đề hallucination, nhu cầu RAG có nguồn kiểm chứng | `K000_PROJECT_OVERVIEW.md`, `K008_ENTERPRISE_RAG_VISION.md` | Có nền |
| 2. Bài toán và câu hỏi nghiên cứu | Phát biểu bài toán, research question: chiến lược chunking nào tốt hơn cho RAG tiếng Việt | `K000_PROJECT_OVERVIEW.md`, `REVIEW_REQUIREMENTS.md` | Có nền |
| 3. Cơ sở lý thuyết | RAG, embedding, vector database, retrieval, source chunks, 4 chiến lược chunking | `K005_RAG_FOUNDATION.md`, `K006_CHUNKING_STRATEGIES.md` | Có nền |
| 4. Kiến trúc hệ thống | Dataset, preprocessing, chunking, embedding, ChromaDB, query pipeline, Streamlit UI | `ARCHITECTURE.md`, `K003_STREAMLIT_DEMO.md`, `K004_REAL_DATASET_DEMO.md` | Có nền |
| 5. Triển khai MVP | Verify, indexing, CLI query, Streamlit demo, real dataset mode, execution patch embedding | `K000_PROJECT_OVERVIEW.md`, `START_HERE.md`, context C-003 đến C-008 | Có nền |
| 6. Đánh giá thực nghiệm | Mô tả RAGAS, metric, cấu hình benchmark, bảng kết quả, biểu đồ so sánh | `K007_EVALUATION_RAGAS.md` | Chưa có kết quả |
| 7. Thảo luận | Phân tích chiến lược tốt nhất, trade-off, lỗi thường gặp, source chunks | Chờ `benchmark_results.csv` thật | Chưa làm |
| 8. Giới hạn và hướng phát triển | Chưa có upload doanh nghiệp, chưa có hybrid/reranking, semantic fallback, API patch | `K008_ENTERPRISE_RAG_VISION.md`, `K010_DEFENSE_ARGUMENTS.md` | Có nền |
| 9. Kết luận | Tóm tắt MVP đã chứng minh gì và phần còn cần hoàn thành | `REVIEW_ACTION_MATRIX.md` | Một phần |

## Placeholder cho kết quả benchmark

Phần này chỉ được điền sau khi có `benchmark_results.csv` thật.

| Strategy | Faithfulness | Answer Relevancy | Context Recall | Context Precision | Avg Score |
|---|---:|---:|---:|---:|---:|
| fixed | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả |
| recursive | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả |
| semantic | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả |
| paragraph | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả | Chờ kết quả |

Ghi chú bắt buộc: RAGAS benchmark chưa hoàn thành, không được claim strategy nào tốt nhất nếu chưa có số liệu thật.

## Giới hạn hiện tại

- Chưa có RAGAS benchmark chính thức.
- Chưa có `benchmark_results.csv`.
- Chưa có kết luận định lượng về strategy tốt nhất.
- Semantic chunking có fallback, cần nêu rõ khi báo cáo.
- Đang dùng execution patch `gemini-embedding-001` vì API key chưa hỗ trợ `text-embedding-004`.
- Chưa xử lý riêng câu hỏi trộn tiếng Việt và tiếng Anh.
- Chưa có upload tài liệu doanh nghiệp thật trong MVP.

## Hướng phát triển Enterprise

- Upload và batch ingestion tài liệu doanh nghiệp.
- Metadata nâng cao, phân quyền, audit log và monitoring.
- Hybrid search, BM25, reranking, GraphRAG.
- Benchmark mở rộng trên nhiều domain tiếng Việt.
- Tối ưu chi phí API, cache embedding và cơ chế chạy offline khi demo.
