# FINAL DEMO SCRIPT — 7 PHÚT

Status: `CANONICAL LOCAL DEMO`

## 0:00–0:40 — Bài toán

“Doanh nghiệp cần hỏi đáp nhanh nhưng mỗi người chỉ được thấy đúng tài liệu mình
có quyền. Vì vậy hệ thống phải vừa truy xuất tốt vừa chặn rò rỉ dữ liệu trước
khi model xử lý.”

## 0:40–1:30 — Kiến trúc

Mở Figma, chỉ đúng một luồng:

```text
User -> Auth/ACL SQL -> Dense + BM25 top-20
     -> fine-tuned Cross-Encoder -> top-5 -> answer + citation
```

Giải thích: BM25 tìm theo từ khóa; Dense tìm theo ý nghĩa; RRF trộn hai danh
sách; Cross-Encoder đọc đồng thời câu hỏi và đoạn văn để xếp hạng kỹ hơn.

## 1:30–3:00 — Đóng góp fine-tune

Mở bảng kết quả:

- no-rerank MRR 0.669;
- base Cross-Encoder 0.779;
- fine-tuned Cross-Encoder 0.945.

Nói rõ: cùng locked test 114 query và cùng Hybrid top-20. Checkpoint chọn theo
validation, không chọn theo test. Không gọi đây là RAGAS.

## 3:00–5:10 — Demo sản phẩm

1. Login admin.
2. Tạo/xem phòng ban và user.
3. Mở tài liệu theo phạm vi.
4. Hỏi một câu; mở citation và chỉ `retrieval.method`.
5. Login user phòng ban khác hoặc dùng test evidence để chứng minh tài liệu
   ngoài quyền không vào candidate set.
6. Mở audit log.

## 5:10–6:10 — Bằng chứng kỹ thuật

- Chạy `python -m pytest tests -q`: 58 pass.
- Docker health: healthy.
- 20 request đồng thời local: 20/20 HTTP 200, p95 khoảng 1.72 giây.

Nói rõ đây là smoke test một máy, không phải cam kết production.

## 6:10–7:00 — Kết luận và giới hạn

“Đóng góp chính là reranker fine-tuned được tích hợp thật vào retrieval, có
đánh giá trước/sau và ACL-first. Hiện MVP chạy local/Docker. Bước tiếp theo là
Supabase/Postgres RLS, public preview và đánh giá generation/RAGAS.”

## Fallback

- Web lỗi: dùng ảnh dashboard/admin và artifact JSON.
- Checkpoint thiếu: demo BM25 fallback, tuyệt đối không nói reranker đang chạy.
- Mạng lỗi: Figma và Docker local vẫn đủ trình bày.
