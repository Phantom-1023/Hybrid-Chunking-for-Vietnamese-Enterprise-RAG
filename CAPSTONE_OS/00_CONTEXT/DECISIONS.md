# DECISIONS

## Vì sao dùng dataset public thay vì upload file tùy ý?

Mission hiện tại là benchmark/demo trên `sailor2/Vietnamese_RAG`, không phải xây hệ thống ingest tài liệu doanh nghiệp. Dataset public giúp demo độc lập, lặp lại được và phù hợp yêu cầu nghiên cứu.

## Vì sao tạm dùng `gemini-embedding-001`?

API key hiện tại không hỗ trợ `text-embedding-004`. Để hoàn thành MVP demo, nhóm dùng execution patch `gemini-embedding-001`. Đây là quyết định runtime tạm thời, không thay đổi mission gốc.

## Vì sao 4 ChromaDB collections riêng?

Mỗi chunking strategy cần được đánh giá độc lập. Nếu trộn chung collection, kết quả retrieval không còn phản ánh đúng strategy. Vì vậy dùng:

- `collection_fixed`
- `collection_recursive`
- `collection_semantic`
- `collection_paragraph`

## Vì sao benchmark không được fake?

North Star của đề tài là bảng RAGAS có căn cứ. Fake benchmark sẽ phá giá trị nghiên cứu và rất dễ bị hỏi khi bảo vệ. Nếu chưa có benchmark, UI phải nói rõ là chưa chạy.

## Vì sao RAGAS/evaluation-lite phải giới hạn?

Gemini API có quota và chi phí. Full evaluation trên nhiều câu hỏi và 4 strategies có thể chậm, tốn quota hoặc làm máy lag. Evaluation-lite nên bắt đầu với số câu nhỏ, có cache, rồi mới mở rộng.
