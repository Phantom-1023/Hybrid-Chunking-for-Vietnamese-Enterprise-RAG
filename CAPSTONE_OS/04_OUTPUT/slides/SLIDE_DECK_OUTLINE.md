# Khung slide Review 2 / bảo vệ

Tài liệu này là outline slide, chưa phải file trình chiếu cuối. Slide benchmark chỉ là placeholder cho đến khi có kết quả RAGAS thật.

| Slide | Tiêu đề | Thông điệp chính | Hình ảnh/bằng chứng cần có | Ghi chú thuyết trình |
|---|---|---|---|---|
| 1 | Tên đề tài | RAG cho quản lý tri thức doanh nghiệp tiếng Việt | Tên đề tài, tên nhóm, GVHD | Mở đầu ngắn, nhấn mạnh tiếng Việt và RAG |
| 2 | Vấn đề | LLM dễ thiếu ngữ cảnh và cần nguồn kiểm chứng | Ví dụ câu hỏi cần tài liệu nguồn | Nói về hallucination và dữ liệu nội bộ |
| 3 | Mục tiêu | So sánh 4 chiến lược chunking trên dataset tiếng Việt | Danh sách fixed, recursive, semantic, paragraph | Nêu rõ đây là MVP benchmark/demo |
| 4 | Góp ý Review 1 | Dataset phải độc lập, cần prototype website, cần pipeline rõ | Trích ý từ `REVIEW_REQUIREMENTS.md` | Chứng minh nhóm đã phản hồi feedback |
| 5 | Dataset | Dùng `sailor2/Vietnamese_RAG`, config `BKAI_RAG` | Screenshot sample record hoặc schema | Nhấn mạnh public dataset có ground truth |
| 6 | Kiến trúc tổng thể | Dataset -> Chunking -> Embedding -> ChromaDB -> Retrieval -> LLM -> UI | Sơ đồ từ `ARCHITECTURE.md` | Giải thích luồng end-to-end |
| 7 | 4 chiến lược chunking | Mỗi strategy tạo collection riêng để so sánh công bằng | Bảng 4 strategy và điểm mạnh/yếu | Nói rõ semantic có fallback nếu được hỏi |
| 8 | Trạng thái MVP | Verify, index, CLI query, Streamlit, real dataset demo đã chạy | Checklist C-003 đến C-008 | Chỉ nói các phần đã có bằng chứng |
| 9 | Demo UI | Người dùng chọn strategy, chọn record thật, hỏi và xem source chunks | Screenshot Streamlit | Nhấn mạnh không phải câu hỏi khóa cứng |
| 10 | Source chunks | Source chunks giúp kiểm tra câu trả lời dựa trên tài liệu nào | Screenshot answer + chunks | Đây là bằng chứng chống hallucination |
| 11 | RAGAS benchmark | Sẽ dùng Faithfulness, Answer Relevancy, Context Recall, Context Precision | Placeholder bảng/biểu đồ | Nói rõ đang pending, chưa có số liệu |
| 12 | Giới hạn hiện tại | Chưa có RAGAS, chưa có upload doanh nghiệp, dùng execution patch embedding | Danh sách giới hạn | Chủ động minh bạch, không claim quá mức |
| 13 | Hướng Enterprise | Upload tài liệu, metadata, phân quyền, hybrid search, reranking, GraphRAG | Roadmap 3 phase | Nói rõ đây là future work |
| 14 | Kế hoạch tiếp theo | Chạy benchmark thật, hoàn thiện report, hoàn thiện slide | Ma trận hành động ưu tiên | Kết nối với Review 2/3 |
| 15 | Q&A | Sẵn sàng trả lời câu hỏi | 3 câu hỏi dự phòng từ `K010_DEFENSE_ARGUMENTS.md` | Chuẩn bị demo fallback CLI |

## Placeholder biểu đồ benchmark

Chỉ chèn biểu đồ khi đã có `benchmark_results.csv` thật.

- Trục X: fixed, recursive, semantic, paragraph.
- Trục Y: `avg_score`.
- Có bảng metric chi tiết phía dưới.
- Nếu chưa có kết quả trước Review 2, slide ghi: "RAGAS benchmark đang pending, không sử dụng số liệu giả."

## Slide cần ưu tiên làm trước

1. Slide 3: mục tiêu và research question.
2. Slide 6: kiến trúc tổng thể.
3. Slide 8: trạng thái MVP.
4. Slide 9-10: demo và source chunks.
5. Slide 11: placeholder benchmark thật.
