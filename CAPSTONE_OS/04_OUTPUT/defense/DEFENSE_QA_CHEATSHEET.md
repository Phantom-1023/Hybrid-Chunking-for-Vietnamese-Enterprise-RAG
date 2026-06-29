# Defense Q&A Cheatsheet

## Project goal

### 1. Dự án của nhóm giải quyết vấn đề gì?

- **Trả lời ngắn:** Dự án xây dựng MVP RAG cho dữ liệu tiếng Việt, tập trung vào việc truy xuất source chunks trước khi sinh câu trả lời. Trọng tâm nghiên cứu hiện tại là so sánh 4 chiến lược chunking trên dataset public.
- **Evidence:** Streamlit demo, `benchmark_results.csv`, `START_HERE.md`.
- **Không overclaim:** Không nói hệ thống đã là sản phẩm doanh nghiệp hoàn chỉnh.

### 2. Câu hỏi nghiên cứu chính là gì?

- **Trả lời ngắn:** Với dữ liệu tiếng Việt, chiến lược chunking nào giúp RAG truy xuất đúng ngữ cảnh hơn: fixed, recursive, semantic hay paragraph? MVP tạo 4 collection riêng để quan sát hành vi retrieval của từng strategy.
- **Evidence:** Slide 3, ChromaDB 4 collections, benchmark tab.
- **Không overclaim:** Không nói đã có kết luận học thuật cuối cùng.

### 3. Vì sao đề tài này có ý nghĩa?

- **Trả lời ngắn:** RAG giúp câu trả lời có căn cứ từ tài liệu nguồn, phù hợp với bài toán tri thức doanh nghiệp. Với tiếng Việt, chunking ảnh hưởng mạnh đến truy xuất nên việc so sánh strategy có ý nghĩa thực nghiệm.
- **Evidence:** Source chunks trong UI, `K008_ENTERPRISE_RAG_VISION.md`.
- **Không overclaim:** Không nói đây là hướng nghiên cứu hoàn toàn mới.

## RAG theory

### 4. RAG là gì?

- **Trả lời ngắn:** RAG là Retrieval-Augmented Generation: hệ thống truy xuất context liên quan trước, sau đó dùng LLM sinh câu trả lời dựa trên context đó. Điểm mạnh là câu trả lời có nguồn để kiểm chứng.
- **Evidence:** Demo answer + source chunks.
- **Không overclaim:** Không nói RAG loại bỏ hallucination 100%.

### 5. Vì sao không chỉ dùng LLM trực tiếp?

- **Trả lời ngắn:** LLM trực tiếp có thể thiếu dữ liệu riêng của bài toán và trả lời không có căn cứ. RAG đưa source chunks vào prompt để câu trả lời bám sát tài liệu hơn.
- **Evidence:** UI hiển thị source chunks.
- **Không overclaim:** Không nói LLM không còn quan trọng.

### 6. Source chunks giúp gì?

- **Trả lời ngắn:** Source chunks cho biết câu trả lời dựa trên đoạn nào. Khi thầy hỏi căn cứ, nhóm có thể mở chunk và metadata để kiểm tra.
- **Evidence:** Streamlit source chunks, CLI query output.
- **Không overclaim:** Không nói cứ có source chunk là answer chắc chắn đúng.

## Chunking strategies

### 7. Vì sao cần chunking?

- **Trả lời ngắn:** Văn bản dài không thể đưa nguyên vào retrieval/generation hiệu quả. Chunking chia văn bản thành đoạn nhỏ hơn để embed, lưu vector và truy xuất đúng phần liên quan.
- **Evidence:** Pipeline slide.
- **Không overclaim:** Không nói chunking là yếu tố duy nhất quyết định chất lượng RAG.

### 8. Fixed chunking là gì?

- **Trả lời ngắn:** Fixed chunking chia văn bản theo kích thước cố định. Nó dễ triển khai và ổn định, nhưng có thể cắt ngang ý hoặc câu.
- **Evidence:** Slide 7, benchmark row fixed.
- **Không overclaim:** Không nói fixed luôn kém.

### 9. Recursive chunking là gì?

- **Trả lời ngắn:** Recursive chunking cố gắng cắt theo cấu trúc tự nhiên như đoạn, câu, rồi mới cắt nhỏ nếu cần. Nó thường giữ ngữ cảnh tốt hơn fixed trong nhiều trường hợp.
- **Evidence:** Slide 7, benchmark row recursive.
- **Không overclaim:** Không nói recursive luôn tốt nhất.

### 10. Semantic chunking có thật không?

- **Trả lời ngắn:** Strategy semantic có tồn tại trong MVP, nhưng có fallback khi xử lý semantic quá nặng hoặc thiếu điều kiện runtime. Nhóm nói rõ đây là giới hạn hiện tại.
- **Evidence:** `K010_DEFENSE_ARGUMENTS.md`, limitation slide.
- **Không overclaim:** Không nói semantic hiện là triển khai semantic đầy đủ.

### 11. Paragraph chunking là gì?

- **Trả lời ngắn:** Paragraph chunking chia theo đoạn văn. Trong evaluation-lite hiện tại, paragraph có tín hiệu tốt nhất vì dataset/context có cấu trúc đoạn phù hợp.
- **Evidence:** `paragraph avg_score = 0.8354`.
- **Không overclaim:** Không nói paragraph chắc chắn thắng trên mọi dataset.

## Dataset

### 12. Vì sao dùng dataset public thay vì dữ liệu doanh nghiệp?

- **Trả lời ngắn:** Dataset public giúp không phụ thuộc quyền dữ liệu doanh nghiệp và có ground truth để đánh giá. Đây cũng phản hồi góp ý Review 1 về dataset backup.
- **Evidence:** `sailor2/Vietnamese_RAG`, real dataset demo.
- **Không overclaim:** Không nói dataset public thay thế hoàn toàn dữ liệu doanh nghiệp thật.

### 13. Dataset đang dùng là gì?

- **Trả lời ngắn:** Dataset là `sailor2/Vietnamese_RAG`, config `BKAI_RAG`. MVP dùng subset nhỏ để verify, index, query và benchmark-lite.
- **Evidence:** UI real dataset tab, `benchmark_results.csv`.
- **Không overclaim:** Không nói đã benchmark toàn bộ dataset.

### 14. Ground truth dùng để làm gì?

- **Trả lời ngắn:** Ground truth dùng để so sánh thủ công với answer và hỗ trợ đánh giá. Trong evaluation-lite, nó còn dùng để tính keyword overlap.
- **Evidence:** Real dataset demo: question, ground_truth, context preview.
- **Không overclaim:** Không nói keyword overlap tương đương đánh giá ngữ nghĩa đầy đủ.

## Architecture

### 15. Kiến trúc hệ thống gồm những bước nào?

- **Trả lời ngắn:** Dataset -> join context -> chunking -> Gemini embedding -> ChromaDB -> query retrieval -> LLM generation -> Streamlit UI. Mỗi strategy có collection riêng.
- **Evidence:** Slide kiến trúc, `START_HERE.md`.
- **Không overclaim:** Không nói có hybrid search/reranking.

### 16. Vì sao dùng ChromaDB?

- **Trả lời ngắn:** ChromaDB local đơn giản, đủ cho MVP nhỏ và có thể tạo 4 collection riêng để so sánh strategy. Nó không cần server phức tạp nên phù hợp demo nhanh.
- **Evidence:** ChromaDB collections, index pass.
- **Không overclaim:** Không nói ChromaDB là lựa chọn production cuối cùng.

### 17. Vì sao mỗi strategy có collection riêng?

- **Trả lời ngắn:** Collection riêng giúp cô lập kết quả retrieval của từng cách chunking. Khi cùng một câu hỏi chạy qua các collection khác nhau, nhóm thấy được strategy nào truy xuất tốt hơn.
- **Evidence:** `collection_fixed`, `collection_recursive`, `collection_semantic`, `collection_paragraph`.
- **Không overclaim:** Không nói chỉ cần collection riêng là so sánh đã hoàn hảo.

## Evaluation

### 18. Benchmark hiện tại là gì?

- **Trả lời ngắn:** Benchmark hiện tại là evaluation-lite trên 5 sample. Nó đo top1 hit, top-k hit, avg distance, keyword overlap và avg_score từ output thật của pipeline.
- **Evidence:** `benchmark_results.csv`.
- **Không overclaim:** Không gọi nó là full RAGAS.

### 19. RAGAS đã hoàn thành chưa?

- **Trả lời ngắn:** Chưa. Nhóm không fake số liệu RAGAS; hiện chỉ có evaluation-lite để kiểm tra nhanh retrieval behavior của MVP.
- **Evidence:** Warning trên UI benchmark tab, `K011_EVALUATION_LITE.md`.
- **Không overclaim:** Không nói có Faithfulness/Answer Relevancy thật nếu chưa chạy.

### 20. Vì sao chỉ 5 samples?

- **Trả lời ngắn:** Vì mục tiêu chiều nay là demo MVP an toàn, tránh quota/API và tránh làm máy lag. 5 mẫu đủ để tạo tín hiệu benchmark thật ban đầu, không đủ để kết luận học thuật cuối cùng.
- **Evidence:** `sample_count = 5` trong CSV.
- **Không overclaim:** Không nói 5 mẫu đại diện toàn bộ dataset.

### 21. Paragraph thắng nghĩa là gì?

- **Trả lời ngắn:** Trong evaluation-lite trên 5 mẫu, paragraph có `avg_score = 0.8354`, cao nhất hiện tại. Điều này cho thấy paragraph đang có tín hiệu retrieval tốt trong subset nhỏ, chưa phải kết luận cuối.
- **Evidence:** Benchmark tab, CSV row paragraph.
- **Không overclaim:** Không nói paragraph chắc chắn là best strategy tổng quát.

### 22. Avg_score được hiểu thế nào?

- **Trả lời ngắn:** `avg_score` là điểm tổng hợp từ proxy metrics của evaluation-lite. Nó giúp nhìn nhanh hành vi retrieval, không phải điểm RAGAS chuẩn.
- **Evidence:** `K011_EVALUATION_LITE.md`.
- **Không overclaim:** Không so sánh avg_score với RAGAS score.

## Demo

### 23. Demo chứng minh được gì?

- **Trả lời ngắn:** Demo chứng minh pipeline end-to-end chạy được: chọn strategy, lấy record thật, hỏi, nhận answer và xem source chunks. Benchmark tab đọc CSV thật và vẽ chart.
- **Evidence:** Streamlit tại `http://localhost:8503`.
- **Không overclaim:** Không nói demo chứng minh hệ thống chính xác ở production.

### 24. Nếu Streamlit lỗi thì sao?

- **Trả lời ngắn:** Nhóm dùng CLI fallback để chứng minh pipeline lõi vẫn chạy. CLI vẫn chọn strategy, query ChromaDB và in answer/source chunks.
- **Evidence:** `python main.py --mode query --strategy fixed --question "..."`
- **Không overclaim:** Không đổ lỗi mơ hồ; nói rõ rủi ro môi trường UI.

## Enterprise angle

### 25. Vì sao gọi là Enterprise RAG?

- **Trả lời ngắn:** Vì hướng ứng dụng là quản lý tri thức doanh nghiệp: tài liệu, chính sách, quy trình, báo cáo. MVP hiện làm phần lõi RAG và source transparency; các tính năng enterprise thật là phase sau.
- **Evidence:** `K008_ENTERPRISE_RAG_VISION.md`.
- **Không overclaim:** Không nói đã có phân quyền, audit log, upload doanh nghiệp.

### 26. Vì sao chưa có upload file doanh nghiệp?

- **Trả lời ngắn:** Upload file nằm ngoài MVP hiện tại. Nhóm ưu tiên dataset public có ground truth để benchmark trước, sau đó mới mở rộng ingestion doanh nghiệp.
- **Evidence:** Mission non-goals, Review response.
- **Không overclaim:** Không nói upload đã sẵn sàng.

## Limitations

### 27. Điểm yếu lớn nhất hiện tại là gì?

- **Trả lời ngắn:** Điểm yếu lớn nhất là full RAGAS chưa hoàn thành và evaluation-lite còn nhỏ. Nhóm đã ghi rõ limitation này và không dùng số liệu giả.
- **Evidence:** UI warning, `K011_EVALUATION_LITE.md`.
- **Không overclaim:** Không né tránh câu hỏi.

### 28. Vì sao dùng `gemini-embedding-001`?

- **Trả lời ngắn:** API key hiện tại không hỗ trợ `text-embedding-004`, nên nhóm dùng execution patch `gemini-embedding-001` để MVP chạy được. Đây là patch runtime, không đổi mission gốc.
- **Evidence:** Execution patch note trong UI.
- **Không overclaim:** Không nói mission đã đổi model.

## Future work

### 29. Bước tiếp theo về khoa học là gì?

- **Trả lời ngắn:** Bước tiếp theo là chạy full RAGAS với Faithfulness, Answer Relevancy, Context Recall và Context Precision trên sample lớn hơn. Sau đó phân tích vì sao strategy thắng dựa trên số liệu.
- **Evidence:** `K011_EVALUATION_LITE.md`, report outline.
- **Không overclaim:** Không nói evaluation-lite đã đủ thay RAGAS.

### 30. Bước tiếp theo về hệ thống là gì?

- **Trả lời ngắn:** Mở rộng ingestion tài liệu, metadata, cache, monitoring, và sau đó thử hybrid search/reranking. Các bước này phục vụ Enterprise RAG thật nhưng không nằm trong MVP chiều nay.
- **Evidence:** `K008_ENTERPRISE_RAG_VISION.md`.
- **Không overclaim:** Không nói đã implement các phần này.
