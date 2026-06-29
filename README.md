# RAG Enterprise System - Review 2 MVP

## Tổng quan

Dự án xây dựng demo RAG để so sánh 4 chiến lược chunking trên dataset tiếng Việt public `sailor2/Vietnamese_RAG`, config `BKAI_RAG`. MVP hiện tại tập trung chứng minh pipeline có thể chạy thật từ verify, indexing, truy vấn, demo Streamlit và benchmark nhẹ.

Mục tiêu nghiên cứu hiện tại: đánh giá ảnh hưởng của chiến lược chunking đến chất lượng retrieval trong RAG tiếng Việt.

## Tính năng MVP hiện có

- Load dataset `sailor2/Vietnamese_RAG`, config `BKAI_RAG`.
- Giới hạn subset 50 records cho indexing/demo.
- Hỗ trợ 4 chunking strategies: `fixed`, `recursive`, `semantic`, `paragraph`.
- Tạo 4 ChromaDB collections riêng: `collection_fixed`, `collection_recursive`, `collection_semantic`, `collection_paragraph`.
- CLI verify, index, query.
- Streamlit demo với câu hỏi thủ công và demo record thật từ dataset.
- Evaluation-lite tạo `benchmark_results.csv` để kiểm tra nhanh retrieval behavior.

## Kiến trúc tóm tắt

Pipeline chính:

1. Dataset loader đọc dữ liệu tiếng Việt public.
2. Chunking module chia context theo 4 strategies.
3. Gemini embedding tạo vector cho chunk và câu hỏi.
4. ChromaDB lưu vector theo từng collection strategy.
5. Retriever lấy top-k source chunks theo strategy được chọn.
6. Generator tạo câu trả lời bằng LLM nếu provider khả dụng.
7. Streamlit UI hiển thị answer, source chunks và benchmark-lite.

## Cài đặt

Tạo môi trường Python rồi cài dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Cấu hình `.env`

Tạo file `.env` từ `.env.example` và điền key thật trên máy local:

```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_EMBEDDING_MODEL=gemini-embedding-001
GEMINI_FLASH_MODEL=gemini-1.5-flash
EMBEDDING_PROVIDER=gemini
EVAL_LIMIT=5
EVAL_USE_LLM_GENERATION=false
```

Lưu ý: MVP đang dùng execution patch `gemini-embedding-001` vì API key hiện tại không hỗ trợ `text-embedding-004`. Không sửa mission gốc để che việc này.

## Chạy verify

```powershell
python main.py --mode verify
```

Lệnh này kiểm tra dataset, schema, sample context, 4 chunking strategies và embedding provider.

## Chạy index

```powershell
python main.py --mode index
```

Lệnh này tạo dữ liệu vector trong `./chroma_db/`. Thư mục này là runtime artifact, không nên commit lên GitHub.

## Chạy query CLI

```powershell
python main.py --mode query --strategy fixed --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

Có thể đổi strategy thành `fixed`, `recursive`, `semantic`, hoặc `paragraph`.

## Chạy evaluation-lite

```powershell
python main.py --mode evaluate-lite
```

Kết quả được ghi vào:

```text
benchmark_results.csv
```

## Evaluation-lite khác RAGAS thế nào?

Evaluation-lite là benchmark nhỏ dùng metric đo được trực tiếp từ retrieval/generation hiện tại, ví dụ `top1_hit_rate`, `topk_hit_rate`, `avg_distance`, `answer_keyword_overlap`, `avg_score`.

Đây không phải full RAGAS. Full RAGAS vẫn là hướng đánh giá chuẩn hơn cho các metric như faithfulness, answer relevancy, context recall và context precision, nhưng chưa hoàn tất trong MVP này để tránh phụ thuộc nặng, quota và thời gian chạy dài.

## Chạy Streamlit demo

```powershell
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
```

Mở trình duyệt tại:

```text
http://localhost:8503
```

UI cho phép chọn strategy, nhập câu hỏi thủ công, chọn record thật từ dataset, xem answer, source chunks và benchmark-lite.

## Giới hạn hiện tại

- Chưa có full RAGAS.
- Benchmark-lite hiện chạy trên sample nhỏ.
- `semantic` có fallback khi semantic chunking đầy đủ quá nặng.
- Đang dùng `gemini-embedding-001` do execution patch.
- Chưa có upload tài liệu doanh nghiệp tùy ý.
- Chưa phải production Enterprise RAG system.

## Enterprise roadmap

- Chạy full RAGAS trên sample lớn hơn.
- Mở rộng ingestion cho tài liệu doanh nghiệp.
- Thêm quản lý quyền truy cập tài liệu.
- Bổ sung Hybrid Search, reranking.
- Nghiên cứu GraphRAG hoặc Agentic RAG như hướng dài hạn.
- Chuẩn hóa deployment, monitoring và audit trail.

## Cảnh báo bảo mật

Không bao giờ commit `.env`, API key, token, `chroma_db/`, dữ liệu raw/temp, log, cache hoặc file cá nhân lên GitHub.

Trước khi push, luôn chạy:

```powershell
git status --short
git check-ignore -v .env
git ls-files .env
```

Nếu `.env` xuất hiện trong staged/tracked files, phải gỡ ra trước khi commit.
