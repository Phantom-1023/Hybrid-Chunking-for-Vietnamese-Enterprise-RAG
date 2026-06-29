# K003 Streamlit Demo

## 1. Streamlit demo dùng để làm gì?

Streamlit demo là giao diện trình bày nhanh cho hội đồng thấy hệ thống RAG đã chạy được các bước tối thiểu: chọn chiến lược chunking, nhập câu hỏi, truy xuất source chunks từ ChromaDB và sinh câu trả lời. Demo này không thay thế benchmark RAGAS, nhưng giúp chứng minh pipeline verify, indexing và query đã hoạt động thật.

## 2. Người dùng chọn strategy và hỏi như thế nào?

Người dùng chọn một trong bốn strategy ở sidebar: fixed, recursive, semantic hoặc paragraph. Sau đó có thể chọn câu hỏi mẫu hoặc nhập câu hỏi riêng trong ô text input, rồi bấm nút “Hỏi hệ thống”. Hệ thống sẽ dùng đúng collection tương ứng với strategy đó để retrieve top-k chunks.

## 3. Source chunks được hiển thị để làm gì?

Source chunks là bằng chứng cho câu trả lời. Mỗi chunk hiển thị nội dung, distance và metadata như record id, strategy, chunk index. Khi bảo vệ, nhóm có thể chỉ ra câu trả lời được tạo dựa trên đoạn dữ liệu nào, tránh cảm giác chatbot trả lời không có căn cứ.

## 4. Nếu chưa có RAGAS thì giải thích với thầy ra sao?

Nếu chưa có file `benchmark_results.csv`, UI hiển thị rõ: “Benchmark RAGAS chưa chạy. MVP hiện tại đã hoàn thành verify, indexing và query pipeline.” Khi thầy hỏi, trả lời rằng demo hiện chứng minh đường chạy kỹ thuật đã hoàn tất; RAGAS là milestone tiếp theo để lượng hóa và so sánh chính thức 4 strategy.

## 5. Nếu thầy hỏi vì sao dùng gemini-embedding-001 thì trả lời gì?

Trả lời rằng mission gốc vẫn là `text-embedding-004`, nhưng API key hiện tại không hỗ trợ model đó. Nhóm dùng execution patch `gemini-embedding-001` để hoàn thành MVP demo và ghi rõ trên UI. Đây là giải pháp tạm thời, không thay đổi mục tiêu nghiên cứu trong báo cáo.
