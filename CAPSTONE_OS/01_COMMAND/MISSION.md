# MISSION.md
> RAG Enterprise — GSU26AI09

---

## Vision

Xây dựng một hệ thống RAG (Retrieval-Augmented Generation) được tối ưu cho văn bản nghiệp vụ tiếng Việt, cung cấp bằng chứng khoa học về hiệu suất của các chiến lược chunking thông qua đánh giá định lượng chuẩn hóa bằng RAGAS.

---

## North Star

> **"Bảng so sánh RAGAS của 4 chiến lược chunking trên tập dữ liệu tiếng Việt, chứng minh rõ ràng chiến lược nào vượt trội — và tại sao."**

Thành công khi hội đồng bảo vệ nhìn vào bảng kết quả và có thể trả lời ngay: *"Đội đã thực nghiệm, đo lường, và rút ra kết luận có căn cứ."*

---

## Success Criteria

| # | Tiêu chí | Mức tối thiểu để pass | Mức lý tưởng |
|---|----------|-----------------------|--------------|
| 1 | 4 chiến lược chunking chạy được | Fixed ✓ Recursive ✓ Semantic ✓ Paragraph ✓ | Kết quả ổn định, không crash |
| 2 | RAGAS evaluation hoàn chỉnh | ≥ 3/4 metrics có kết quả | Đủ 4 metrics: Faithfulness, Answer Relevancy, Context Recall, Context Precision |
| 3 | So sánh có ý nghĩa | Kết quả khác nhau giữa các chiến lược | Có biểu đồ + nhận xét phân tích |
| 4 | Demo chạy được live | Streamlit không crash khi GV hỏi | Q&A hoạt động + hiện chunk được dùng |
| 5 | Báo cáo đủ nộp | Đủ chương, đủ hình | Bảng kết quả RAGAS được chèn vào report |
| 6 | Dataset độc lập | Không phụ thuộc dữ liệu doanh nghiệp | `sailor2/Vietnamese_RAG` (public HuggingFace) |

---

## Scope

**Trong phạm vi đề tài:**

- So sánh **4 chiến lược chunking**: Fixed-size, Recursive, Semantic, Paragraph
- **Embedding**: Gemini `text-embedding-004` (Google API)
- **LLM sinh câu trả lời**: Gemini Flash (Google API)
- **Vector store**: ChromaDB (local, 4 collection riêng biệt cho 4 chiến lược)
- **Đánh giá**: RAGAS metrics trên `sailor2/Vietnamese_RAG` (BKAI_RAG config, 50 documents)
- **Giao diện**: Streamlit — Q&A demo + bảng benchmark
- **Preprocessing cơ bản**: join passages từ `List[str]` → `str`, loại bỏ khoảng trắng thừa
- **Xử lý mixed Việt-Anh**: ghi nhận là giới hạn, không chặn hệ thống (dùng tokenizer mặc định)

**Ngoài phạm vi (đã xác nhận cắt):**

Xem phần Non-goals bên dưới.

---

## Non-goals

> Những thứ này **không** nằm trong scope — không implement, không demo, không báo cáo.

| Hạng mục | Lý do cắt |
|----------|-----------|
| BM25 / Hybrid Retrieval | Ngoài research question; không đủ thời gian |
| Re-ranking (cross-encoder) | Thêm biến số không kiểm soát được vào benchmark |
| Docker / containerization | Không cần thiết cho academic demo |
| Multi-user authentication | UI chỉ cần chạy được cho GV demo |
| Ingest file doanh nghiệp thật | Dataset đã giải quyết bằng public dataset |
| Fine-tune embedding model | API-first constraint — không train local |
| Hierarchical chunking | Không trong 4 chiến lược đã cam kết |
| Production deployment | Đây là prototype nghiên cứu |
| Xử lý auto-translate mixed text | Ghi nhận là hướng mở rộng trong báo cáo |
