# K004 Demo Với Dataset Thật

## 1. Vì sao demo bằng dataset public là demo thật?

Demo bằng `sailor2/Vietnamese_RAG` là demo thật vì câu hỏi, đáp án và ngữ cảnh đều đến từ một dataset public, không phải nội dung tự bịa trong UI. Hệ thống phải load record, dùng câu hỏi gốc, truy xuất chunks từ ChromaDB đã index và sinh câu trả lời theo pipeline RAG hiện tại.

## 2. Ground truth dùng để làm gì?

Ground truth là đáp án tham chiếu của dataset. Trong demo, ground truth được đặt cạnh generated answer để người xem so sánh thủ công. Đây chưa phải RAGAS, nhưng giúp kiểm tra nhanh câu trả lời có đúng ý chính hay không.

## 3. Generated answer so với ground truth như thế nào?

Generated answer là câu trả lời do LLM sinh ra từ source chunks được retrieval. Ground truth là đáp án chuẩn của dataset. Nếu generated answer khớp các ý chính trong ground truth, pipeline retrieval và generation đang hoạt động tốt. Nếu lệch, nhóm có thể xem source chunks để biết lỗi đến từ retrieval hay generation.

## 4. Source chunks chứng minh điều gì?

Source chunks chứng minh hệ thống không trả lời ngẫu nhiên. Mỗi chunk hiển thị nội dung và metadata như strategy, record id, chunk index. Khi bảo vệ, nhóm có thể chỉ ra câu trả lời dựa trên đoạn dữ liệu nào trong dataset.

## 5. Nếu thầy hỏi “sao không upload file?” thì trả lời gì?

Trả lời rằng MVP hiện tại tập trung đúng mission: so sánh 4 chiến lược chunking trên dataset tiếng Việt public. Upload file doanh nghiệp thật nằm ngoài phạm vi hiện tại và có thể làm lệch mục tiêu benchmark. Demo dataset public giúp kết quả độc lập, lặp lại được và phù hợp với yêu cầu nghiên cứu.
