# Checklist handoff cho team

## Mỗi teammate phải đọc gì?

- Đọc siêu nhanh 10 phút: `CAPSTONE_OS/02_KNOWLEDGE/START_HERE.md`
- Người làm slide: `CAPSTONE_OS/04_OUTPUT/slides/SLIDE_CONTENT.md`
- Người nói chính: `CAPSTONE_OS/04_OUTPUT/slides/SLIDE_SPEAKER_SCRIPT.md`
- Người demo: `CAPSTONE_OS/04_OUTPUT/rehearsal/DEMO_REHEARSAL_CHECKLIST.md`
- Người trả lời benchmark: `CAPSTONE_OS/02_KNOWLEDGE/learning/K011_EVALUATION_LITE.md`
- Người trả lời enterprise/future work: `CAPSTONE_OS/02_KNOWLEDGE/learning/K008_ENTERPRISE_RAG_VISION.md`
- Người bắt buộc phải thay thế phút chót: đọc file này và `ONE_SPEAKER_7_MIN_SCRIPT.md`

## Ai trình bày phần nào?

- **Người 1 - mở đầu:** vấn đề, mục tiêu, research question, dataset.
- **Người 2 - kỹ thuật:** kiến trúc, 4 chunking strategy, ChromaDB collections.
- **Người 3 - demo:** điều khiển Streamlit, chọn record thật, chạy query, mở source chunks.
- **Người 4 - evaluation:** giải thích evaluation-lite, số benchmark và lý do chưa full RAGAS.
- **Người 5 - kết luận:** limitations, execution patch, enterprise vision, future work.

Nếu chỉ có một người nói: dùng `ONE_SPEAKER_7_MIN_SCRIPT.md`.

## Ai điều khiển demo?

- Một người duy nhất điều khiển chuột/bàn phím.
- Một người đứng cạnh đọc checklist demo.
- Không để nhiều người cùng click.
- Không chạy lại index hoặc benchmark khi đang trình bày.
- Nếu máy lag, dừng thao tác 5-10 giây, không click liên tục.

## Ai trả lời technical questions?

Người kỹ thuật nên nắm:

- Pipeline: dataset -> chunking -> embedding -> ChromaDB -> retrieval -> LLM -> UI.
- 4 collection riêng: fixed, recursive, semantic, paragraph.
- Source chunks dùng để kiểm chứng answer.
- Semantic chunking có fallback trong MVP.
- Execution patch `gemini-embedding-001` là tạm thời do API key chưa hỗ trợ `text-embedding-004`.

## Ai trả lời evaluation questions?

Người evaluation nên nắm:

- Benchmark hiện là evaluation-lite, không phải full RAGAS.
- Sample count là 5.
- Paragraph có `avg_score = 0.8354`.
- Không kết luận học thuật cuối cùng từ evaluation-lite.
- Full RAGAS sẽ dùng Faithfulness, Answer Relevancy, Context Recall, Context Precision ở bước tiếp theo.

## Ai trả lời câu hỏi enterprise?

Người kết luận/future work nên nắm:

- MVP hiện làm phần lõi Enterprise RAG.
- Dataset public dùng để có ground truth và tránh phụ thuộc dữ liệu doanh nghiệp đóng.
- Upload file doanh nghiệp, phân quyền, audit log, hybrid search, reranking, GraphRAG là phase sau.
- Không nói hệ thống đã production-ready.

## Emergency one-page summary

Dự án là MVP RAG tiếng Việt để so sánh 4 chiến lược chunking: fixed, recursive, semantic, paragraph. Dataset dùng là `sailor2/Vietnamese_RAG`, config `BKAI_RAG`, public và có ground truth. Hệ thống đã có verify, index ChromaDB, CLI query, Streamlit demo, real dataset demo và evaluation-lite benchmark.

Demo chính mở tại:

```text
http://localhost:8503
```

Lệnh chạy nếu cần:

```powershell
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
```

Fallback CLI:

```powershell
python main.py --mode query --strategy fixed --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

Số benchmark cần nhớ:

- fixed: `avg_score = 0.3344`
- recursive: `avg_score = 0.3410`
- semantic: `avg_score = 0.3313`
- paragraph: `avg_score = 0.8354`

Câu nói an toàn:

"Đây là evaluation-lite trên 5 mẫu, chưa phải full RAGAS. Kết quả dùng để kiểm tra nhanh retrieval behavior trong MVP. Nhóm không dùng số liệu giả và không claim hệ thống đã production-ready."

## Nếu teammate vắng mặt

- Người còn lại đọc `ONE_SPEAKER_7_MIN_SCRIPT.md`.
- Bỏ bớt slide chi tiết, giữ 5 ý: vấn đề, pipeline, demo, benchmark-lite, limitations/future work.
- Nếu không demo được UI, dùng CLI fallback và nói source chunks là bằng chứng pipeline.
