# K001 Verify Và Indexing

## 1. Khái niệm: Verify mode và Indexing pipeline là gì?

Verify mode là bước kiểm tra đầu vào trước khi xây hệ thống RAG đầy đủ. Lệnh `python main.py --mode verify` dùng để xác nhận dataset tải được, schema đúng, context được nối thành văn bản sạch, 4 chiến lược chunking đều tạo được chunk, và cấu hình Gemini embedding có thể được kiểm tra.

Indexing pipeline là bước biến dữ liệu văn bản thành dữ liệu tìm kiếm vector. Pipeline đọc dataset, chia văn bản thành chunks, gọi embedding model để đổi mỗi chunk thành vector, rồi lưu vector cùng metadata vào ChromaDB. Đây là nền tảng để các bước retrieval, sinh câu trả lời và đánh giá RAGAS chạy sau này.

## 2. Dự án dùng như thế nào?

Dự án dùng dataset public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`, chọn tối đa 50 records. Mỗi record có `context`, `question` và `answer`. Trường `context` được nối thành một chuỗi text sạch, sau đó được chunk bằng 4 chiến lược: fixed, recursive, semantic và paragraph.

Lệnh verify dùng để kiểm tra nhanh dữ liệu và chunker. Lệnh index dùng để tạo ChromaDB local tại `./chroma_db/`, với 4 collection tương ứng 4 chiến lược. Kết quả index là điều kiện cần cho milestone retrieval và RAGAS evaluation.

## 3. Vì sao dùng 4 ChromaDB collections riêng?

Mục tiêu nghiên cứu là so sánh công bằng 4 chiến lược chunking. Nếu dùng chung một collection, chunk của các chiến lược có thể bị trộn lẫn, làm kết quả retrieval và RAGAS không còn phản ánh đúng từng strategy.

Vì vậy dự án dùng 4 collection riêng:

- `collection_fixed`
- `collection_recursive`
- `collection_semantic`
- `collection_paragraph`

Cách này giúp cô lập kết quả, dễ đếm số vector, dễ query thử từng strategy, và dễ giải thích khi đưa số liệu vào báo cáo.

## 4. Vì sao cần embedding trước retrieval?

Retrieval trong RAG cần tìm các đoạn context liên quan nhất với câu hỏi. Máy không thể so sánh trực tiếp ý nghĩa của văn bản nếu chỉ nhìn chuỗi ký tự. Embedding chuyển câu hỏi và chunks thành vector số trong cùng một không gian ngữ nghĩa.

Khi đã có vector, hệ thống có thể dùng similarity search để tìm top-k chunks gần câu hỏi nhất. Đây là đầu vào cho Gemini Flash sinh câu trả lời và là dữ liệu để RAGAS đánh giá faithfulness, relevancy, recall và precision.

## 5. Nếu thầy hỏi thì trả lời gì?

Nếu thầy hỏi verify mode để làm gì, trả lời: “Verify mode kiểm tra dataset, preprocessing, chunking và Gemini embedding trước khi chạy pipeline nặng hơn.”

Nếu thầy hỏi vì sao phải index, trả lời: “Indexing biến chunks thành vectors và lưu vào ChromaDB để hệ thống truy xuất được context liên quan khi người dùng đặt câu hỏi.”

Nếu thầy hỏi vì sao 4 collection riêng, trả lời: “Để mỗi chiến lược chunking được đánh giá độc lập, không bị trộn dữ liệu, từ đó bảng RAGAS phản ánh đúng hiệu quả từng strategy.”

Nếu thầy hỏi semantic fallback là gì, trả lời: “Trong milestone đầu, semantic strategy vẫn tồn tại và tạo chunk ổn định bằng fallback nhẹ. Đây là lựa chọn để demo không bị chặn bởi model semantic nặng; phần này được ghi rõ là giới hạn kỹ thuật.”
