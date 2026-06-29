# Ôn gấp trước khi vào phòng

## Project trong 5 dòng

1. Đây là MVP RAG cho dữ liệu tiếng Việt.
2. Dataset: `sailor2/Vietnamese_RAG`, config `BKAI_RAG`.
3. Mục tiêu: so sánh 4 chunking strategy: fixed, recursive, semantic, paragraph.
4. Demo đã có: Streamlit, real dataset record, answer, source chunks, benchmark tab.
5. Benchmark hiện là evaluation-lite, chưa phải full RAGAS.

## Demo trong 5 bước

1. Mở `http://localhost:8503`.
2. Chọn strategy, ưu tiên `paragraph` khi nói về benchmark.
3. Mở tab "Demo với dữ liệu thật", chọn/random record.
4. Bấm "Hỏi bằng câu hỏi này", mở answer và source chunks.
5. Mở "Benchmark evaluation-lite", chỉ bảng, chart và warning chưa full RAGAS.

## 5 số cần nhớ

1. Sample count: `5`.
2. fixed `avg_score = 0.3344`.
3. recursive `avg_score = 0.3410`.
4. semantic `avg_score = 0.3313`.
5. paragraph `avg_score = 0.8354`.

## 5 claim nguy hiểm cần tránh

1. Không nói: "Đã hoàn thành full RAGAS."
2. Không nói: "Paragraph chắc chắn tốt nhất trên mọi dữ liệu."
3. Không nói: "Hệ thống đã production-ready cho doanh nghiệp."
4. Không nói: "Đã có upload file doanh nghiệp."
5. Không nói: "Semantic chunking đã là bản đầy đủ không fallback."

## 5 câu trả lời mạnh nhất

1. **Dự án là gì?**  
   "MVP RAG tiếng Việt để so sánh 4 chiến lược chunking, có demo end-to-end và source chunks để kiểm chứng."

2. **Vì sao dataset public?**  
   "Dataset public giúp không phụ thuộc dữ liệu doanh nghiệp đóng và có ground truth để benchmark."

3. **Vì sao chưa RAGAS?**  
   "Nhóm không fake số liệu; hiện có evaluation-lite thật để kiểm tra MVP, full RAGAS là bước tiếp theo."

4. **Vì sao gọi Enterprise RAG?**  
   "Vì hướng ứng dụng là quản lý tri thức doanh nghiệp; MVP hiện làm lõi RAG, production features là phase sau."

5. **Benchmark nói gì?**  
   "Trong evaluation-lite trên 5 mẫu, paragraph có tín hiệu tốt nhất với `avg_score = 0.8354`, nhưng chưa phải kết luận học thuật cuối cùng."

## Câu chốt an toàn

"MVP hiện chạy được end-to-end trên dataset public tiếng Việt, có source chunks và benchmark-lite thật. Nhóm minh bạch rằng full RAGAS và enterprise production là bước tiếp theo, không phải phần đã hoàn thành."
