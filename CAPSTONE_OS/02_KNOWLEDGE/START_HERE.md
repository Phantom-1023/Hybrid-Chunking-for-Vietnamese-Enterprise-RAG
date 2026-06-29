# Bắt đầu đọc từ đây

Đây là bản đồ đọc trung tâm cho thư mục `CAPSTONE_OS/02_KNOWLEDGE/`. File này chỉ chỉ đường, không thay thế nội dung chi tiết ở các artifact khác.

## Trạng thái dự án trong 10 dòng

1. Dự án là RAG demo cho dữ liệu tiếng Việt.
2. Dataset chính: `sailor2/Vietnamese_RAG`, config `BKAI_RAG`.
3. Mục tiêu nghiên cứu: so sánh 4 chiến lược chunking.
4. 4 strategy hiện có: fixed, recursive, semantic, paragraph.
5. Verify dataset/chunking đã pass.
6. ChromaDB indexing đã pass với 4 collection riêng.
7. CLI query đã pass.
8. Streamlit demo đã pass, có mode dùng record thật từ dataset public.
9. Execution patch hiện tại: dùng `gemini-embedding-001` vì API key chưa hỗ trợ `text-embedding-004`.
10. RAGAS benchmark, `benchmark_results.csv`, final report và final slides chưa hoàn thành.

## Bản đồ thư mục

- `architecture/`: kiến trúc hệ thống, pipeline indexing/query/evaluation.
- `review/`: yêu cầu Review 1/2/3 và ma trận hành động.
- `learning/`: kiến thức ngắn để học, viết report, trả lời bảo vệ.
- `research/`: tài liệu nghiên cứu tham khảo, có cả hướng mở rộng ngoài MVP.
- `K001...K004...`: artifact theo các task verify, indexing, query, Streamlit và real dataset demo.

## Thứ tự đọc

### Đọc khẩn cấp 15 phút

1. `learning/K000_PROJECT_OVERVIEW.md`
2. `review/REVIEW_ACTION_MATRIX.md`
3. `learning/K010_DEFENSE_ARGUMENTS.md`
4. `architecture/ARCHITECTURE.md`

Mục tiêu: nắm dự án đang ở đâu, còn thiếu gì, và trả lời được câu hỏi cơ bản của thầy.

### Đọc nghiêm túc 60 phút

1. `learning/K000_PROJECT_OVERVIEW.md`
2. `learning/K005_RAG_FOUNDATION.md`
3. `learning/K006_CHUNKING_STRATEGIES.md`
4. `learning/K007_EVALUATION_RAGAS.md`
5. `learning/K008_ENTERPRISE_RAG_VISION.md`
6. `review/REVIEW_REQUIREMENTS.md`
7. `review/REVIEW_ACTION_MATRIX.md`
8. `architecture/ARCHITECTURE.md`

Mục tiêu: đủ nền để viết report, sửa slide và giải thích quyết định kỹ thuật.

### Chuẩn bị bảo vệ đầy đủ

1. Đọc toàn bộ nhóm `learning/`.
2. Đọc `review/REVIEW_REQUIREMENTS.md` để biết GV từng góp ý gì.
3. Đọc `review/REVIEW_ACTION_MATRIX.md` để biết mục nào đã xong, mục nào còn thiếu.
4. Đọc `architecture/ARCHITECTURE.md` để vẽ pipeline.
5. Đọc `research/RESEARCH SUMMARY.docx` như tài liệu tham khảo hướng mở rộng, không claim đã làm.
6. Đọc các artifact demo `K001` đến `K004` nếu cần bằng chứng từng milestone.

## File phục vụ từng việc

| Việc cần làm | File nên đọc |
|---|---|
| Làm slide | `K000_PROJECT_OVERVIEW.md`, `K006_CHUNKING_STRATEGIES.md`, `K008_ENTERPRISE_RAG_VISION.md`, `ARCHITECTURE.md`, `REVIEW_ACTION_MATRIX.md` |
| Viết report | `K005_RAG_FOUNDATION.md`, `K006_CHUNKING_STRATEGIES.md`, `K007_EVALUATION_RAGAS.md`, `REVIEW_REQUIREMENTS.md`, `ARCHITECTURE.md` |
| Chạy demo | `K003_STREAMLIT_DEMO.md`, `K004_REAL_DATASET_DEMO.md`, `CAPSTONE_OS/00_CONTEXT/RUNBOOK.md` |
| Trả lời Q&A bảo vệ | `K010_DEFENSE_ARGUMENTS.md`, `K008_ENTERPRISE_RAG_VISION.md`, `REVIEW_ACTION_MATRIX.md` |
| Phản hồi review | `REVIEW_REQUIREMENTS.md`, `REVIEW_ACTION_MATRIX.md`, `K000_PROJECT_OVERVIEW.md` |

## Mục còn thiếu hiện tại

- RAGAS benchmark: chưa làm.
- `benchmark_results.csv`: chưa có.
- Final report: chưa xác nhận hoàn thiện.
- Final slides: chưa xác nhận hoàn thiện.

## Nhiệm vụ đề xuất tiếp theo

1. C-011B: tạo outline report và slide từ các artifact hiện có, để trống phần benchmark.
2. C-012: chạy evaluation-lite/RAGAS giới hạn nhỏ, có log thật và không fake kết quả.
3. C-013: tạo `benchmark_results.csv` thật và cập nhật Streamlit benchmark tab.
4. C-014: hoàn thiện chương kết quả report dựa trên bảng benchmark thật.
5. C-015: hoàn thiện slide bảo vệ 12-15 trang, có demo flow và biểu đồ benchmark.
