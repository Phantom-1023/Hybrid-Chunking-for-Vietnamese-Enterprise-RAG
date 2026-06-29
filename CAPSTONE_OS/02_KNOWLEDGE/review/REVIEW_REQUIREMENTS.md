# Tổng hợp yêu cầu Review

Nguồn: `AI_Capstone_Review123_GSU26AI09.xlsx`, gồm 3 sheet: `Review1`, `Review2`, `Review3`.

## Review 1 requirements

- Bài toán phải rõ ràng: hệ thống RAG cho quản lý tri thức doanh nghiệp tiếng Việt.
- Dataset phải có phương án backup, không phụ thuộc hoàn toàn vào dữ liệu doanh nghiệp.
- Cần làm rõ dataset doanh nghiệp có được phép mở/sử dụng hay không.
- Cần đẩy nhanh xử lý và ưu tiên hướng có thể chạy được.
- Cần có hướng xử lý văn bản hoặc câu hỏi nửa tiếng Việt, nửa tiếng Anh, ví dụ translator hoặc API trung gian.
- Kết quả mong muốn có thể là báo cáo khoa học/paper.
- Software hoàn chỉnh: Review 1 ghi nhận là chưa có.
- Software prototype: cần có website/demo.
- Framework/API được nhắc: FAISS, LangChain, LlamaIndex, Chroma, Docker, Streamlit.
- Kiến trúc được gợi ý: RAG pipeline.
- Hướng tìm hiểu ban đầu: 3 chiến lược chunking, 3 phương pháp truy xuất, 2 thuật toán reranking.
- Cần chứng minh giá trị thực tế và ý nghĩa khoa học, đặc biệt ở bài toán chunking tiếng Việt.

## Review 1 teacher comments

- Dataset phải thu thập backup, không phụ thuộc doanh nghiệp.
- Cần kiểm tra quyền mở/sử dụng dataset doanh nghiệp.
- Đẩy nhanh xử lý.
- Có phương án cho văn bản/người dùng dùng lẫn tiếng Việt và tiếng Anh.
- Software hoàn chỉnh: chưa đạt.
- Prototype nên có website.
- Đề tài có tính thực tiễn và có ý nghĩa khoa học về chunking tiếng Việt.
- Đề tài không mới hoàn toàn, nhưng giải quyết vấn đề chưa có giải pháp hiệu quả.

## Review 2 requirements

Sheet Review2 chủ yếu là form tiêu chí, chưa thấy nhận xét cụ thể của giảng viên. Các mục cần chuẩn bị:

- Nêu thay đổi sau Review 1 và cách nhóm phản hồi feedback.
- Có kế hoạch/quản trị dự án đầy đủ.
- Trình bày phương pháp quản trị và công cụ hỗ trợ.
- Với từng hướng tiếp cận: giải thích cách thu thập và chuẩn bị dữ liệu.
- Với từng hướng tiếp cận: giải thích mô hình, đặc trưng, biểu diễn dữ liệu, thuật toán và thiết kế.
- Với từng hướng tiếp cận: giải thích huấn luyện/đánh giá, độ phức tạp, tinh chỉnh tham số và cải tiến.

## Review 2 teacher comments

- Chưa có comment cụ thể trong file Excel. Cần kiểm tra thủ công nếu GV đã ghi ở bản khác.

## Review 3 requirements

Sheet Review3 cũng chủ yếu là form tiêu chí, chưa thấy nhận xét cụ thể ngoài các dòng gợi ý chung. Các mục cần chuẩn bị:

- Nêu thay đổi sau Review 2.
- Chứng minh kế hoạch và quản trị dự án.
- Đánh giá kết quả của các phương pháp/hướng tiếp cận đã đặt ra.
- So sánh các phương pháp, thảo luận và kết luận.
- Hoàn thiện report.
- Bổ sung tinh chỉnh models nếu có cơ sở.
- Chỉnh sửa demo.
- Tăng độ chính xác model.
- Chuẩn bị đủ bằng chứng để được khuyến nghị bảo vệ lần 1.

## Grading/rubric requirements

- Review3 có các mức khuyến nghị: đủ tiêu chuẩn bảo vệ lần 1; cần cập nhật theo góp ý để bảo vệ lần 1; thiếu sót nhiều và phải bảo vệ lần 2; thiếu sót nghiêm trọng và nên chấm dứt dự án.
- File không có điểm số/rubric định lượng cụ thể. Cần kiểm tra thủ công nếu có rubric riêng ngoài workbook này.

## Dự án phải thể hiện

- Demo RAG chạy được, tốt nhất là website/Streamlit.
- Dataset public hoặc dataset được phép dùng, không phụ thuộc dữ liệu doanh nghiệp đóng.
- RAG pipeline rõ: dataset, chunking, embedding, vector store, retrieval, generation.
- So sánh các chiến lược chunking bằng bằng chứng định lượng.
- Nêu được ý nghĩa khoa học của chunking tiếng Việt.
- Trả lời được vì sao không làm các phần ngoài MVP như upload file doanh nghiệp, hybrid search, reranking hoặc GraphRAG ở giai đoạn hiện tại.

## Dự án phải nộp

- Report khoa học hoàn chỉnh.
- Slide bảo vệ có vấn đề, research question, kiến trúc, demo, kết quả và kết luận.
- Bằng chứng chạy demo.
- Bảng/biểu đồ benchmark khi hoàn thành RAGAS.
- Tài liệu giải thích các quyết định kỹ thuật và giới hạn hiện tại.

## Mục còn thiếu hoặc cảnh báo rõ ràng

- RAGAS/benchmark chưa hoàn thành trong trạng thái hiện tại.
- Report và slide chưa được xác nhận hoàn thiện.
- Chưa có xử lý câu hỏi trộn tiếng Việt/tiếng Anh trong MVP.
- Chưa có hybrid retrieval/reranking; đây là hướng mở rộng, không nằm trong MVP hiện tại.
- Semantic chunking hiện có fallback, cần nói rõ trong báo cáo/demo nếu được hỏi.
