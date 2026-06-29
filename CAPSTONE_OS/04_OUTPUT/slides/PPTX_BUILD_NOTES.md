# PPTX Build Notes

File PowerPoint: `CAPSTONE_OS/04_OUTPUT/slides/RAG_ENTERPRISE_REVIEW2.pptx`

Ghi chú chung: Deck dùng phong cách học thuật gọn, nền sáng, màu navy/blue/teal nhất quán. Benchmark trong deck là evaluation-lite trên 5 mẫu, chưa phải full RAGAS.

## Slide 1: Title

Nói ngắn: Giới thiệu đề tài RAG Enterprise Demo, trọng tâm là so sánh 4 chunking strategy trên dataset tiếng Việt. Nhấn mạnh MVP demo được, đo được và không fake benchmark.

## Slide 2: Problem: Vietnamese Enterprise RAG

Nói ngắn: LLM cần nguồn kiểm chứng khi trả lời câu hỏi nghiệp vụ. RAG giúp đưa source chunks vào câu trả lời để người xem có thể đối chiếu.

## Slide 3: Research Question

Nói ngắn: Câu hỏi nghiên cứu là strategy nào hỗ trợ retrieval tốt hơn cho RAG tiếng Việt. Bốn strategy được so sánh là fixed, recursive, semantic và paragraph.

## Slide 4: Review 1 Response

Nói ngắn: Nhóm đã phản hồi góp ý Review 1 bằng dataset public, Streamlit demo và pipeline rõ. Những phần ngoài MVP không được claim.

## Slide 5: Dataset: sailor2/Vietnamese_RAG

Nói ngắn: Dataset public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`, giúp không phụ thuộc dữ liệu doanh nghiệp đóng và có ground truth để đánh giá.

## Slide 6: System Architecture

Nói ngắn: Pipeline là dataset -> chunking -> embedding -> ChromaDB -> query -> answer. Mỗi bước đã có trong MVP và có thể demo được.

## Slide 7: Four Chunking Strategies

Nói ngắn: Fixed đơn giản, recursive giữ cấu trúc tốt hơn, semantic hiện có fallback, paragraph phù hợp khi văn bản có cấu trúc đoạn. Không nói strategy nào thắng tổng quát.

## Slide 8: Indexing Pipeline

Nói ngắn: Chunks được embed và lưu vào 4 ChromaDB collections riêng. Collection riêng giúp so sánh strategy rõ hơn.

## Slide 9: Query Pipeline + Source Evidence

Nói ngắn: Khi hỏi, hệ thống embed câu hỏi, retrieve top-k chunks và sinh answer từ context. Source chunks là bằng chứng bảo vệ câu trả lời.

## Slide 10: Streamlit Demo

Nói ngắn: UI có manual question, real dataset demo và benchmark tab. Khi demo, ưu tiên real dataset tab để chứng minh không dùng câu hỏi khóa cứng.

## Slide 11: Evaluation-lite Benchmark

Nói ngắn: Slide này có chart `avg_score`: fixed 0.3344, recursive 0.3410, semantic 0.3313, paragraph 0.8354. Nói rõ: evaluation-lite trên 5 mẫu, chưa phải full RAGAS.

## Slide 12: Result: paragraph currently best in MVP

Nói ngắn: Paragraph đang cao nhất trong evaluation-lite hiện tại, nhưng đây chỉ là tín hiệu MVP. Không kết luận học thuật cuối cùng khi chưa có full RAGAS và sample lớn hơn.

## Slide 13: Limitations

Nói ngắn: Giới hạn bắt buộc phải nói: chưa full RAGAS, sample nhỏ, semantic fallback, execution patch `gemini-embedding-001`, chưa production enterprise upload.

## Slide 14: Enterprise Roadmap

Nói ngắn: Roadmap gồm full RAGAS, tăng sample size, upload enterprise documents, Hybrid Search, Reranking, GraphRAG/Agentic RAG. Đây là future work, không phải phần đã hoàn thành.

## Slide 15: Conclusion + Next Steps

Nói ngắn: MVP đã chạy end-to-end, có source chunks và benchmark-lite thật. Bước tiếp theo là full RAGAS, hoàn thiện report và slide final.

## Cảnh báo khi trình bày

- Không nói evaluation-lite là full RAGAS.
- Không nói paragraph chắc chắn là strategy tốt nhất tổng quát.
- Không nói hệ thống đã production-ready cho doanh nghiệp.
- Không nói đã hỗ trợ upload tài liệu doanh nghiệp.
- Không che giấu execution patch `gemini-embedding-001`.
