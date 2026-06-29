# Tầm nhìn Enterprise RAG

## Vì sao gọi là Enterprise RAG?

Bài toán hướng tới quản lý tri thức doanh nghiệp: hợp đồng, quy trình, báo cáo, chính sách nội bộ và tài liệu vận hành. RAG phù hợp vì doanh nghiệp cần trả lời dựa trên nguồn tài liệu cụ thể, có thể kiểm chứng.

## Hiện tại đã làm phần nào?

MVP hiện tại làm phần lõi:

- Load dataset tiếng Việt public.
- Chunking theo 4 chiến lược.
- Embedding và lưu vào ChromaDB.
- Retrieval theo strategy.
- Sinh answer bằng LLM.
- Streamlit demo hiển thị answer và source chunks.

## Doanh nghiệp thật sẽ mở rộng ra sao?

Sau MVP, hệ thống có thể thêm upload tài liệu doanh nghiệp, phân quyền, metadata nâng cao, audit log, cache, monitoring, batch ingestion và deployment.

## Upload enterprise documents nằm ở phase nào?

Upload file doanh nghiệp nằm ở phase sau MVP. MVP hiện tại dùng dataset public để tránh phụ thuộc quyền dữ liệu doanh nghiệp và để có ground truth phục vụ benchmark.

## Hướng mở rộng

GraphRAG, Hybrid Search, BM25, reranking và hierarchical chunking là hướng mở rộng. Những phần này không nằm trong MVP hiện tại, không nên claim đã làm trong report hoặc defense.
