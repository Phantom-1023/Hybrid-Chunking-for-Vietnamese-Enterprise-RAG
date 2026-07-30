# ÔN NHANH TRƯỚC KHI BẢO VỆ

Status: `CANONICAL / EVIDENCE-LOCKED`

## Dự án trong 5 câu

1. Đây là MVP RAG tiếng Việt cho tri thức doanh nghiệp có citation và ACL.
2. ACL/RLS lọc tài liệu trước khi retriever hoặc reranker nhìn thấy dữ liệu.
3. Dense + BM25 hợp nhất bằng RRF để lấy top-20 candidate.
4. Phần được fine-tune là Cross-Encoder reranker: top-20 → top-5 evidence.
5. Hệ thống có local/Docker runtime, Supabase live canary và Render preview;
   chưa phải production.

## 5 số phải nhớ

1. Dataset/split: `1.141 = 913 train + 114 validation + 114 test`.
2. No-rerank MRR: `0.669`.
3. MMR MRR: `0.699`.
4. Base Cross-Encoder MRR: `0.779`.
5. Fine-tuned Cross-Encoder: `MRR 0.945`, `Hit@1 0.930`, `Hit@5 0.974`.

Tất cả bốn phương án dùng cùng locked test và cùng Hybrid RRF top-20.

## Pipeline nói trong 15 giây

```text
User JWT → SQL RLS/ACL → Dense + BM25 → RRF top-20
         → fine-tuned Cross-Encoder → top-5 → answer/citation
```

BM25 tìm từ khóa chính xác. Dense tìm câu cùng nghĩa. RRF trộn thứ hạng.
Cross-Encoder đọc đồng thời query và passage để xếp hạng kỹ hơn.

## Fine-tune phải giải thích thế nào?

- Không fine-tune BM25 và không fine-tune chatbot LLM.
- Fine-tune Cross-Encoder bằng các cặp `(query, passage, relevance)`.
- Checkpoint chọn theo validation ở epoch 1; test không dùng để chọn model.
- Có training history, reload test, weights-changed check và checksum.
- SHA256 checkpoint bắt đầu `3782daf` và kết thúc `aa44`.

## Nếu bị hỏi leakage

“Nhóm khóa seed 42, tách query 913/114/114 và kiểm tra không có duplicate
question hoặc query-passage pair conflict giữa split. Phạm vi kết luận là query
generalization trên cùng corpus, chưa phải document generalization.”

## Nếu bị hỏi ACL có thật không

“Ngoài unit/integration test local, nhóm chạy live canary trên Supabase bằng hai
phòng HR và Finance. Mỗi user chỉ list/retrieve được document phòng mình. Canary
cũng phát hiện lịch sử chat client còn lại khi đổi user; nhóm đã sửa và regression
canary public pass.”

## 5 claim cấm

1. Không nói benchmark hiện tại là full RAGAS.
2. Không nói đã chứng minh document-domain generalization.
3. Không nói production-ready hoặc chịu tải bền vững 20 user.
4. Không nói public preview đang chạy fine-tuned checkpoint lớn.
5. Không nói Figma đã là production design system.

## Câu kết

“Đóng góp chính của nhóm là đưa fine-tuned Cross-Encoder vào query pipeline thật,
đo trước/sau trên cùng locked test và kết hợp ACL-first để tài liệu ngoài quyền
không đi vào retrieval. Sản phẩm đã có web, Docker, Supabase canary và public
preview; các giới hạn production và generation evaluation được công khai.”
