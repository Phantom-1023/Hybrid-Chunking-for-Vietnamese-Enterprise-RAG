# Script 7 phút cho một người nói chính

Mục tiêu: một người có thể trình bày mạch lạc, demo được, không overclaim RAGAS hoặc enterprise production.

## 0:00-0:30 — Slide 1: Tên đề tài

Chào thầy/cô, đề tài của em là hệ thống RAG cho quản lý tri thức doanh nghiệp trong bối cảnh tiếng Việt. Ở MVP hiện tại, nhóm tập trung vào phần lõi: dataset public tiếng Việt, 4 chiến lược chunking, ChromaDB, truy vấn, Streamlit demo và benchmark evaluation-lite. Mục tiêu là chứng minh hệ thống chạy được và có số liệu thật ban đầu, không dùng benchmark giả.

## 0:30-1:00 — Slide 2: Vấn đề

Với tài liệu tiếng Việt, câu hỏi thường cần đúng đoạn nguồn. Nếu chỉ hỏi LLM trực tiếp, mô hình có thể trả lời tự tin nhưng thiếu căn cứ. RAG giải quyết bằng cách truy xuất source chunks trước, rồi dùng các đoạn đó làm context để sinh câu trả lời. Vì vậy demo của nhóm luôn hiển thị answer cùng source chunks.

## 1:00-1:30 — Slide 3: Câu hỏi nghiên cứu

Câu hỏi nghiên cứu là: chiến lược chunking nào giúp RAG tiếng Việt truy xuất đúng ngữ cảnh hơn? Nhóm so sánh fixed, recursive, semantic và paragraph. Mỗi strategy có một collection riêng trong ChromaDB để việc so sánh rõ ràng hơn.

## 1:30-2:00 — Slide 4-5: Review response và dataset

Ở Review 1, nhóm nhận góp ý về dataset độc lập, prototype website và pipeline rõ. Nhóm phản hồi bằng dataset public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`, có ground truth và không phụ thuộc dữ liệu doanh nghiệp đóng. UI có thể chọn hoặc random record thật, nên demo không phải câu hỏi khóa cứng.

## 2:00-2:40 — Slide 6-7: Kiến trúc và chunking

Pipeline gồm: load dataset, join context, chia chunk theo 4 strategy, embed bằng Gemini, lưu vào ChromaDB, khi hỏi thì embed query, retrieve top-k chunks và dùng LLM sinh answer. Fixed đơn giản nhưng có thể cắt ngang ý. Recursive giữ cấu trúc tốt hơn. Semantic hiện có fallback để đảm bảo demo chạy được. Paragraph chia theo đoạn văn và hiện cho tín hiệu tốt trong benchmark-lite.

## 2:40-3:10 — Slide 8: Trạng thái MVP

Đến hiện tại, MVP đã có verify mode, ChromaDB index, CLI query, Streamlit demo, real dataset demo và evaluation-lite benchmark CSV. Đây là các phần đã chạy được. Phần chưa claim là full RAGAS và enterprise production.

## 3:10-5:00 — Chuyển sang demo live

Mở `http://localhost:8503`.

Nói khi mở UI: Đây là giao diện Streamlit demo. Trên đầu có note execution patch: hiện dùng `gemini-embedding-001` vì API key chưa hỗ trợ `text-embedding-004`; đây là patch runtime, không đổi mission.

Thao tác:

1. Chọn strategy `paragraph` ở sidebar.
2. Mở tab "Demo với dữ liệu thật".
3. Random hoặc chọn một record.
4. Chỉ vào `record_id`, question, ground truth, context preview.
5. Bấm "Hỏi bằng câu hỏi này".
6. Khi answer hiện ra, mở source chunks.

Nói trong lúc source chunks hiện: Đây là điểm quan trọng của RAG. Câu trả lời không đứng một mình mà có source chunks để kiểm chứng. Ground truth cho phép so sánh thủ công câu trả lời với dữ liệu gốc.

## 5:00-5:50 — Slide 11-12 hoặc benchmark tab

Chuyển sang tab "Benchmark evaluation-lite".

Nói: Đây là benchmark nhỏ thật, chưa phải full RAGAS. Nhóm chạy 5 sample để kiểm tra retrieval behavior. Kết quả `avg_score`: fixed 0.3344, recursive 0.3410, semantic 0.3313, paragraph 0.8354. Trong evaluation-lite này paragraph tốt nhất, nhưng nhóm không kết luận học thuật cuối cùng vì full RAGAS chưa chạy.

Giải thích metric nhanh: `top1_hit_rate` và `topk_hit_rate` kiểm tra truy xuất đúng record. `avg_distance` là khoảng cách retrieval. `answer_keyword_overlap` là overlap keyword với ground truth, lần này dùng retrieved source chunks để tránh quota LLM trong benchmark.

## 5:50-6:30 — Slide 13: Limitations

Nhóm minh bạch các giới hạn: full RAGAS chưa chạy; evaluation-lite chỉ 5 mẫu; semantic chunking có fallback; embedding đang dùng execution patch `gemini-embedding-001`; chưa có upload tài liệu doanh nghiệp thật. Đây là lý do nhóm gọi hiện tại là MVP, không phải hệ thống production.

## 6:30-6:50 — Slide 14: Future work

Hướng Enterprise sau MVP gồm upload và batch ingestion tài liệu doanh nghiệp, metadata nâng cao, phân quyền, audit log, monitoring, hybrid search, reranking và GraphRAG. Các phần này là định hướng mở rộng, không claim đã hoàn thành.

## 6:50-7:00 — Slide 15: Kết luận

Tóm lại, MVP đã chứng minh RAG end-to-end chạy được trên dataset public tiếng Việt, có source chunks để kiểm chứng và có benchmark-lite thật. Bước tiếp theo là full RAGAS, hoàn thiện report và slide final. Em xin chuyển sang phần Q&A.

## Câu cấm nói

- Không nói: "Đã hoàn thành RAGAS."
- Không nói: "Paragraph chắc chắn tốt nhất."
- Không nói: "Hệ thống đã production-ready."
- Không nói: "Đã hỗ trợ upload tài liệu doanh nghiệp."
