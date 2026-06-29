# Lập luận bảo vệ

## 1. Dự án giải quyết vấn đề gì?

Trả lời: Dự án xây dựng RAG cho dữ liệu tiếng Việt và so sánh các chiến lược chunking để xem cách nào hỗ trợ truy xuất và trả lời tốt hơn.

Evidence: `MISSION.md`, Streamlit demo, source chunks.

## 2. Vì sao dùng dataset public thay vì dữ liệu doanh nghiệp?

Trả lời: Dataset public giúp demo không phụ thuộc quyền dữ liệu doanh nghiệp, có ground truth để đánh giá và đáp ứng góp ý Review 1 về backup dataset.

Evidence: `sailor2/Vietnamese_RAG`, real dataset demo.

## 3. Vì sao phải chọn strategy khi hỏi?

Trả lời: Mỗi strategy có collection riêng trong ChromaDB. Chọn strategy giúp so sánh cùng câu hỏi trên các cách chunking khác nhau.

Evidence: 4 ChromaDB collections.

## 4. Source chunks dùng để làm gì?

Trả lời: Source chunks cho thấy câu trả lời dựa trên đoạn nào, giúp kiểm tra hallucination và tăng tính minh bạch.

Evidence: UI/CLI hiển thị top source chunks.

## 5. RAGAS đã xong chưa?

Trả lời: Chưa. MVP hiện đã hoàn thành verify, indexing, query và demo. RAGAS là bước tiếp theo để có benchmark định lượng, không fake kết quả.

Evidence: chưa có `benchmark_results.csv`.

## 6. Vì sao hiện dùng `gemini-embedding-001`?

Trả lời: API key hiện tại không hỗ trợ `text-embedding-004`, nên demo dùng execution patch tạm thời `gemini-embedding-001` để hoàn thành MVP. Mission không bị đổi.

Evidence: execution patch note trong demo/context.

## 7. Semantic chunking có thật không?

Trả lời: Strategy semantic tồn tại, nhưng trong MVP có fallback khi xử lý semantic quá nặng hoặc thiếu điều kiện runtime. Khi báo cáo phải nói rõ fallback này.

Evidence: verify/index logs và source note.

## 8. Vì sao chưa làm upload file?

Trả lời: Upload file doanh nghiệp nằm ngoài MVP. Giai đoạn này cần benchmark trên dataset public có ground truth trước, sau đó mới mở rộng ingestion doanh nghiệp.

Evidence: Mission non-goals, `K004_REAL_DATASET_DEMO.md`.

## 9. Vì sao không làm hybrid search/reranking ngay?

Trả lời: Review 1 có nhắc đây là hướng tìm hiểu, nhưng MVP hiện ưu tiên chứng minh 4 chunking strategies và RAGAS. Hybrid/reranking là future work để tránh mở rộng scope quá nhanh.

Evidence: Mission non-goals, plan milestone.

## 10. Demo chứng minh được gì?

Trả lời: Demo chứng minh pipeline end-to-end: dataset thật, chunking, ChromaDB retrieval, LLM answer và source chunks. Phần còn thiếu là benchmark định lượng để kết luận strategy tốt nhất.

Evidence: Streamlit demo, CLI query, context files C-003 đến C-008.
