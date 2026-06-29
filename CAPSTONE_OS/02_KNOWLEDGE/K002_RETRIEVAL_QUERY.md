# K002 Retrieval Và Query Pipeline

## 1. Retrieval là gì?

Retrieval là bước tìm các đoạn văn bản liên quan nhất với câu hỏi của người dùng. Trong hệ thống RAG, câu hỏi được chuyển thành embedding vector, sau đó so sánh với các vector chunks đã lưu trong ChromaDB. Kết quả trả về là top-k source chunks có độ gần ngữ nghĩa cao nhất.

## 2. Query pipeline trong dự án chạy như thế nào?

Pipeline query tối thiểu chạy theo luồng:

1. Người dùng chọn strategy và nhập câu hỏi.
2. Hệ thống embed câu hỏi bằng cùng embedding provider/model đã dùng khi indexing.
3. Hệ thống mở ChromaDB local tại `./chroma_db/`.
4. Strategy được map sang collection tương ứng.
5. ChromaDB trả về top-k source chunks.
6. Hệ thống thử sinh câu trả lời bằng LLM provider sẵn có.
7. Nếu LLM không chạy được, hệ thống vẫn hiển thị retrieval-only answer và các source chunks.

## 3. Vì sao phải chọn strategy khi hỏi?

Mission của dự án là so sánh 4 chiến lược chunking. Mỗi strategy có collection riêng: fixed, recursive, semantic và paragraph. Khi hỏi, phải chọn strategy để biết hệ thống sẽ truy vấn collection nào. Điều này giúp kết quả retrieval phản ánh đúng chất lượng của từng cách chunking.

## 4. Source chunks giúp bảo vệ câu trả lời ra sao?

Source chunks là bằng chứng cho câu trả lời. Khi demo, hội đồng có thể xem câu trả lời được sinh ra từ đoạn context nào, metadata của chunk là gì, và chunk đến từ strategy nào. Nếu answer chưa tốt, source chunks vẫn cho thấy pipeline retrieval đang hoạt động thật, không phải trả lời bịa.

## 5. Nếu thầy hỏi thì trả lời gì?

Nếu thầy hỏi retrieval là gì, trả lời: “Retrieval là bước tìm các đoạn context liên quan nhất bằng vector similarity trước khi sinh câu trả lời.”

Nếu thầy hỏi vì sao phải chọn strategy, trả lời: “Vì mỗi strategy được index vào một collection riêng để so sánh công bằng hiệu quả chunking.”

Nếu thầy hỏi source chunks có vai trò gì, trả lời: “Source chunks là bằng chứng giúp kiểm tra câu trả lời có dựa trên dữ liệu hay không.”

Nếu thầy hỏi khi LLM lỗi thì sao, trả lời: “Hệ thống vẫn hiển thị các chunks truy xuất được, nên demo retrieval không bị sập và vẫn chứng minh được pipeline tìm kiếm hoạt động.”
