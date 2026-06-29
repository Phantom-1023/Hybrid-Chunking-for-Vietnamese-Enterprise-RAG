# CURRENT_STATE

## Mission trong 5 dòng

- Xây dựng demo RAG cho tiếng Việt trên dataset public `sailor2/Vietnamese_RAG`.
- So sánh 4 chiến lược chunking: fixed, recursive, semantic, paragraph.
- Dùng ChromaDB local với 4 collection riêng để cô lập từng strategy.
- Dùng Gemini cho embedding/generation trong demo MVP.
- Mục tiêu cuối là có benchmark RAGAS thật, không fake số liệu.

## Trạng thái kỹ thuật hiện tại

- Verify mode chạy được: `python main.py --mode verify`.
- Index mode đã tạo `./chroma_db/` với 4 collection, mỗi collection hiện có 20 chunks do giới hạn quota.
- Query CLI chạy được: `python main.py --mode query --strategy fixed --question "..."`
- Streamlit demo chạy được tại `http://localhost:8503`.
- UI có hỏi thủ công, demo record thật từ dataset public, source chunks và placeholder benchmark.

## Task đã pass

- C-003: Verify dataset, context join, 4 chunking strategies, Gemini key handling.
- C-004: ChromaDB indexing pipeline và 4 collections.
- C-005: Execution patch `gemini-embedding-001`, index MVP pass.
- C-006: CLI query pipeline pass.
- C-007: Streamlit demo tối thiểu pass.
- C-008: Demo bằng record thật từ dataset public pass.

## Execution patch hiện tại

- Runtime đang dùng `GEMINI_EMBEDDING_MODEL=gemini-embedding-001`.
- Lý do: API key hiện tại không hỗ trợ `text-embedding-004`.
- Đây là patch tạm để demo MVP, không đổi mission gốc.

## Lệnh demo hiện tại

```bat
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
```

Mở: `http://localhost:8503`

## Giới hạn đã biết

- Semantic chunking đang dùng fallback.
- ChromaDB hiện index 20 chunks mỗi strategy để tránh quota Gemini.
- Chưa có RAGAS, chưa có `benchmark_results.csv`.
- Không upload file tùy ý vì ngoài scope MVP hiện tại.
- Không chạy full index/benchmark nếu chưa có PM approval.
