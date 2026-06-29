# Brief thuyết trình cho team

## Dự án là gì?

Dự án là MVP hệ thống RAG cho dữ liệu tiếng Việt, hướng tới bài toán quản lý tri thức doanh nghiệp. Trọng tâm hiện tại là so sánh 4 chiến lược chunking trên dataset public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`, bằng demo chạy thật và benchmark evaluation-lite.

## Đã hoàn thành

- Verify dataset và 4 chunking strategy.
- Index vào ChromaDB với 4 collection: fixed, recursive, semantic, paragraph.
- CLI query theo strategy.
- Streamlit demo.
- Demo bằng record thật từ dataset public.
- Evaluation-lite benchmark và `benchmark_results.csv`.
- Benchmark tab trong UI đọc CSV thật, có bảng và biểu đồ `avg_score`.

## Đang pending

- Full RAGAS chưa chạy.
- Chưa có kết luận học thuật cuối cùng về strategy tốt nhất.
- Chưa có upload tài liệu doanh nghiệp thật.
- Chưa có hybrid search, reranking, GraphRAG.
- Semantic chunking hiện có fallback.
- Embedding đang dùng execution patch `gemini-embedding-001`.

## Mỗi thành viên có thể nói gì?

- **Người mở đầu:** Nói vấn đề, mục tiêu, research question, vì sao dùng RAG.
- **Người kỹ thuật:** Nói pipeline dataset -> chunking -> embedding -> ChromaDB -> retrieval -> LLM -> UI.
- **Người demo:** Chạy Streamlit, chọn strategy, mở real dataset demo, hỏi bằng record thật, chỉ source chunks.
- **Người benchmark:** Nói evaluation-lite, metric, số liệu hiện tại, và nhấn mạnh chưa phải RAGAS.
- **Người kết luận:** Nói giới hạn, execution patch, Enterprise future work và bước tiếp theo.

## Demo flow 5-7 phút

1. Mở `http://localhost:8503`.
2. Chỉ note execution patch `gemini-embedding-001`.
3. Chọn strategy ở sidebar, ưu tiên `paragraph` khi demo benchmark vì đang có điểm cao nhất trong evaluation-lite.
4. Mở tab "Demo với dữ liệu thật".
5. Random hoặc chọn một record.
6. Chỉ vào `record_id`, original question, ground truth, context preview.
7. Bấm "Hỏi bằng câu hỏi này".
8. Mở answer và source chunks.
9. Chuyển sang tab "Benchmark evaluation-lite".
10. Chỉ bảng, bar chart, best strategy và warning chưa phải full RAGAS.

## Số liệu evaluation-lite cần nhớ

| Strategy | Sample count | Top1 hit | Top-k hit | Avg distance | Keyword overlap | Avg score |
|---|---:|---:|---:|---:|---:|---:|
| fixed | 5 | 0.2000 | 0.2000 | 0.8711 | 0.4033 | 0.3344 |
| recursive | 5 | 0.2000 | 0.2000 | 0.8722 | 0.4299 | 0.3410 |
| semantic | 5 | 0.2000 | 0.2000 | 0.8720 | 0.3912 | 0.3313 |
| paragraph | 5 | 0.8000 | 1.0000 | 0.8118 | 0.9897 | 0.8354 |

Kết luận an toàn: "Trong evaluation-lite trên 5 mẫu, paragraph đang cho tín hiệu tốt nhất theo `avg_score`. Đây là kết quả nhỏ để kiểm tra MVP, chưa phải kết luận full RAGAS."

## Giải thích execution patch

Câu trả lời ngắn: "Mission gốc dùng `text-embedding-004`, nhưng API key hiện tại không hỗ trợ model đó. Để MVP chạy được trong demo, nhóm tạm dùng `gemini-embedding-001`. Đây là execution patch, không thay đổi mission và được ghi rõ trong UI."

Không nói: "Nhóm đã đổi mission sang model mới."

## Giải thích enterprise angle

Câu trả lời ngắn: "MVP hiện làm phần lõi Enterprise RAG: dữ liệu, chunking, embedding, vector store, retrieval, generation và source transparency. Các phần doanh nghiệp thật như upload file, phân quyền, audit log, hybrid search và reranking là phase mở rộng sau MVP."

Không nói: "Hệ thống đã sẵn sàng triển khai production cho doanh nghiệp."

## Trả lời: Vì sao chưa full RAGAS?

Câu trả lời ngắn: "Full RAGAS cần thêm dependency/model, có thể chậm và tốn quota API. Nhóm không fake số liệu, nên trước mắt dùng evaluation-lite thật trên tập nhỏ để kiểm tra retrieval behavior. Full RAGAS là bước tiếp theo để có đánh giá học thuật đầy đủ."

Nếu bị hỏi thêm: "Nhóm đã chuẩn bị metric RAGAS mục tiêu gồm Faithfulness, Answer Relevancy, Context Recall và Context Precision; hiện chưa claim các metric đó đã hoàn thành."

## Câu chốt nên dùng

"MVP hiện chứng minh hệ thống RAG end-to-end chạy được trên dataset public tiếng Việt, có source chunks để kiểm chứng và có benchmark-lite thật. Nhóm minh bạch rằng full RAGAS và các tính năng enterprise production là bước tiếp theo, không phải phần đã hoàn thành."
