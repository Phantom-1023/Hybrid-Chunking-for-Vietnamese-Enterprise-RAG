# Nội dung slide đề xuất

## Slide 1: Tên đề tài

- **Thông điệp chính:** Dự án xây dựng MVP RAG cho dữ liệu tiếng Việt, tập trung vào so sánh chunking.
- **Nội dung trên slide:**
  - Retrieval-Augmented Generation System for Enterprise Knowledge Management in Vietnamese Business Contexts
  - Trọng tâm: RAG demo, dataset public tiếng Việt, 4 chiến lược chunking
  - Mục tiêu: demo được, đo được, không fake benchmark
- **Gợi ý hình ảnh:** Tiêu đề lớn + sơ đồ nhỏ Dataset -> RAG -> Answer + Source.
- **Bằng chứng/artifact:** `K000_PROJECT_OVERVIEW.md`, `START_HERE.md`.

## Slide 2: Vấn đề

- **Thông điệp chính:** LLM cần nguồn tri thức kiểm chứng khi trả lời câu hỏi nghiệp vụ.
- **Nội dung trên slide:**
  - Dữ liệu tiếng Việt thường dài, phân tán và khó truy xuất đúng đoạn.
  - LLM có thể trả lời thiếu căn cứ nếu không có context.
  - RAG giúp đưa source chunks vào câu trả lời.
- **Gợi ý hình ảnh:** Before/after: hỏi LLM trực tiếp so với hỏi qua RAG.
- **Bằng chứng/artifact:** `K008_ENTERPRISE_RAG_VISION.md`.

## Slide 3: Câu hỏi nghiên cứu

- **Thông điệp chính:** Dự án hỏi: chunking strategy nào hỗ trợ RAG tiếng Việt tốt hơn?
- **Nội dung trên slide:**
  - So sánh 4 strategy: fixed, recursive, semantic, paragraph.
  - Cùng dataset, cùng embedding provider, 4 collection riêng.
  - Đánh giá ban đầu bằng evaluation-lite; full RAGAS là bước tiếp theo.
- **Gợi ý hình ảnh:** Bảng 4 strategy.
- **Bằng chứng/artifact:** `K000_PROJECT_OVERVIEW.md`, `K011_EVALUATION_LITE.md`.

## Slide 4: Phản hồi Review 1

- **Thông điệp chính:** MVP hiện tại bám sát góp ý: dataset độc lập, prototype website, pipeline rõ.
- **Nội dung trên slide:**
  - Dataset public, không phụ thuộc dữ liệu doanh nghiệp đóng.
  - Có Streamlit demo.
  - Có pipeline verify, index, query, benchmark-lite.
  - Không claim các phần ngoài MVP.
- **Gợi ý hình ảnh:** Checklist Done / Pending.
- **Bằng chứng/artifact:** `REVIEW_ACTION_MATRIX.md`.

## Slide 5: Dataset

- **Thông điệp chính:** Dataset public giúp demo thật và có ground truth để đánh giá.
- **Nội dung trên slide:**
  - Dataset: `sailor2/Vietnamese_RAG`
  - Config: `BKAI_RAG`
  - Subset MVP: tối đa 50 records
  - Demo UI có chọn/random record thật
- **Gợi ý hình ảnh:** Screenshot UI record thật: question, ground_truth, context preview.
- **Bằng chứng/artifact:** `DEMO_SCRIPT.md`, `K000_PROJECT_OVERVIEW.md`.

## Slide 6: Kiến trúc MVP

- **Thông điệp chính:** Hệ thống đã có luồng RAG end-to-end.
- **Nội dung trên slide:**
  - Dataset -> join context -> chunking
  - Gemini embedding -> ChromaDB
  - Query -> retrieval top-k -> Gemini answer
  - Streamlit hiển thị answer và source chunks
- **Gợi ý hình ảnh:** Sơ đồ pipeline ngang.
- **Bằng chứng/artifact:** `SLIDE_DECK_OUTLINE.md`, `START_HERE.md`.

## Slide 7: Bốn chiến lược chunking

- **Thông điệp chính:** Mỗi strategy tạo collection riêng để so sánh hành vi retrieval.
- **Nội dung trên slide:**
  - Fixed: chia theo kích thước cố định.
  - Recursive: ưu tiên cấu trúc tự nhiên.
  - Semantic: có strategy, hiện có fallback trong MVP.
  - Paragraph: chia theo đoạn văn.
- **Gợi ý hình ảnh:** 4 cột strategy.
- **Bằng chứng/artifact:** `K011_EVALUATION_LITE.md`, `START_HERE.md`.

## Slide 8: Trạng thái đã hoàn thành

- **Thông điệp chính:** MVP hiện tại đã đủ để demo live.
- **Nội dung trên slide:**
  - Verify mode: pass.
  - ChromaDB index: 4 collection.
  - CLI query: pass.
  - Streamlit demo: pass.
  - Real dataset demo: pass.
  - Evaluation-lite CSV: có thật.
- **Gợi ý hình ảnh:** Checklist theo task C-003 đến C-013.
- **Bằng chứng/artifact:** `CURRENT_STATE.md`, `START_HERE.md`.

## Slide 9: Demo UI

- **Thông điệp chính:** Người dùng có thể chọn strategy, hỏi câu hỏi và xem nguồn.
- **Nội dung trên slide:**
  - Sidebar chọn chunking strategy.
  - Manual question tab.
  - Real dataset demo tab.
  - Benchmark evaluation-lite tab.
- **Gợi ý hình ảnh:** Screenshot Streamlit.
- **Bằng chứng/artifact:** `DEMO_SCRIPT.md`, `ui/app.py`.

## Slide 10: Source chunks

- **Thông điệp chính:** Source chunks giúp bảo vệ câu trả lời và giảm nguy cơ hallucination.
- **Nội dung trên slide:**
  - Answer luôn đi kèm top source chunks.
  - Metadata giúp truy vết record/chunk.
  - Ground truth hỗ trợ so sánh thủ công ở demo dữ liệu thật.
- **Gợi ý hình ảnh:** Screenshot answer + expanded source chunks.
- **Bằng chứng/artifact:** `DEMO_SCRIPT.md`.

## Slide 11: Evaluation-lite benchmark

- **Thông điệp chính:** Đã có benchmark nhỏ, thật, nhưng chưa phải full RAGAS.
- **Nội dung trên slide:**
  - Evaluation type: `evaluation-lite`
  - Sample count: 5
  - Best theo `avg_score`: paragraph = 0.8354
  - fixed = 0.3344, recursive = 0.3410, semantic = 0.3313
  - Ghi rõ: chưa phải full RAGAS
- **Gợi ý hình ảnh:** Bar chart `avg_score` theo strategy.
- **Bằng chứng/artifact:** `benchmark_results.csv`, `K011_EVALUATION_LITE.md`.

## Slide 12: Cách đọc số benchmark

- **Thông điệp chính:** Số liệu dùng để kiểm tra nhanh retrieval behavior, không dùng để kết luận học thuật cuối cùng.
- **Nội dung trên slide:**
  - `top1_hit_rate`: chunk đầu có đúng record không.
  - `topk_hit_rate`: top-k có đúng record không.
  - `avg_distance`: khoảng cách truy xuất trung bình.
  - `answer_keyword_overlap`: overlap keyword với ground truth.
  - `avg_score`: tổng hợp proxy metrics.
- **Gợi ý hình ảnh:** Bảng giải thích metric.
- **Bằng chứng/artifact:** `K011_EVALUATION_LITE.md`.

## Slide 13: Giới hạn hiện tại

- **Thông điệp chính:** Nhóm minh bạch những gì chưa hoàn thành.
- **Nội dung trên slide:**
  - Chưa có full RAGAS.
  - Evaluation-lite chỉ chạy 5 mẫu.
  - Semantic chunking có fallback.
  - Đang dùng execution patch `gemini-embedding-001`.
  - Chưa có upload tài liệu doanh nghiệp thật.
- **Gợi ý hình ảnh:** Danh sách limitations.
- **Bằng chứng/artifact:** `START_HERE.md`, `K011_EVALUATION_LITE.md`.

## Slide 14: Tầm nhìn Enterprise

- **Thông điệp chính:** MVP là phần lõi; Enterprise production là phase sau.
- **Nội dung trên slide:**
  - Upload và batch ingestion tài liệu doanh nghiệp.
  - Metadata, phân quyền, audit log, monitoring.
  - Hybrid search, reranking, GraphRAG là hướng mở rộng.
  - Không claim các phần này đã hoàn thành.
- **Gợi ý hình ảnh:** Roadmap: MVP -> Evaluation -> Enterprise Expansion.
- **Bằng chứng/artifact:** `K008_ENTERPRISE_RAG_VISION.md`.

## Slide 15: Kết luận và bước tiếp theo

- **Thông điệp chính:** MVP đã chứng minh pipeline chạy được; bước kế tiếp là full evaluation và hoàn thiện báo cáo.
- **Nội dung trên slide:**
  - Đã demo được RAG end-to-end.
  - Đã có benchmark-lite thật.
  - Tiếp theo: full RAGAS, report final, slide final.
  - Cam kết: không fake số liệu, không overclaim.
- **Gợi ý hình ảnh:** Checklist Done / Next.
- **Bằng chứng/artifact:** `REVIEW_ACTION_MATRIX.md`, `benchmark_results.csv`.
