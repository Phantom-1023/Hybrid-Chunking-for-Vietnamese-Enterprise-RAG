# SCRIPT BẢO VỆ 7 PHÚT — MỘT NGƯỜI NÓI

Status: `CANONICAL / KHỚP DECK 11 SLIDE`

## 0:00–0:35 — Slide 1: Mở bài

“Đề tài của em là Vietnamese Enterprise RAG. Bài toán không chỉ là trả lời đúng,
mà còn phải tìm đúng bằng chứng tiếng Việt và bảo đảm người dùng chỉ thấy tài
liệu mình có quyền. Đóng góp chính là fine-tuned Cross-Encoder đã được đưa vào
query pipeline thật, không chỉ tồn tại ở training script.”

## 0:35–1:05 — Slide 2: Vấn đề

“Tìm kiếm chỉ bằng từ khóa có thể bỏ sót cách diễn đạt cùng nghĩa. Dense retrieval
có thể bỏ sót mã hoặc tên chính xác. Nếu evidence yếu, LLM vẫn có thể trả lời rất
trôi chảy. Trong doanh nghiệp còn một rủi ro lớn hơn: tài liệu đúng nhưng sai
quyền truy cập.”

## 1:05–1:40 — Slide 3: Đóng góp fine-tune

“Nhóm không fine-tune BM25 và không fine-tune chatbot LLM. Nhóm fine-tune
Cross-Encoder reranker nhận cặp query–passage. Dense và BM25 tạo top-20 candidate;
reranker chấm lại và chọn top-5 evidence. Checkpoint có training history, reload
test, checksum và before/after metrics.”

## 1:40–2:10 — Slide 4: Pipeline

“Luồng xử lý là: User JWT vào SQL RLS/ACL trước; sau đó BM25 và Dense retrieval;
RRF trộn hai ranking; fine-tuned Cross-Encoder rerank; cuối cùng chỉ top-5 được
đưa tới answer/citation. Vì ACL đứng đầu, model không nhận được document bị cấm.”

## 2:10–2:40 — Slide 5: Data và split

“Dataset có 1.141 query, chia seed 42 thành 913 train, 114 validation và 114 test.
Nhóm kiểm tra không trùng question hoặc query-passage pair giữa split. Checkpoint
chỉ chọn theo validation. Phạm vi là query generalization trên cùng corpus, chưa
phải document generalization.”

## 2:40–3:25 — Slide 6: Kết quả

“Trên cùng locked test và cùng Hybrid top-20: no-rerank MRR 0.669; MMR 0.699;
base Cross-Encoder 0.779; fine-tuned Cross-Encoder 0.945. Fine-tuned Hit@1 là
0.930 và Hit@5 là 0.974. Đây là retrieval evaluation, không phải full RAGAS.”

## 3:25–3:55 — Slide 7: Audit trail

“Training chạy 2 epoch, 572 optimization step. Checkpoint tốt nhất là epoch 1
theo validation. Weights-changed và reload đều pass. Error analysis top-5 có
109 hit→hit, 2 miss→hit, 3 miss→miss và không có hit→miss. Validation 1.0 là dấu
hiệu bão hòa nên nhóm không dùng nó làm claim cải thiện.”

## 3:55–4:35 — Slide 8: ACL

“MVP có admin, manager, member và scope organization, department, private.
Supabase Auth cấp JWT; Postgres RLS là ranh giới bảo mật. Live canary dùng HR và
Finance đã chứng minh hai chiều không list hoặc retrieve tài liệu chéo phòng.
Canary còn giúp nhóm phát hiện và sửa việc chat cũ còn trên client khi đổi user.”

## 4:35–5:30 — Slide 9: Demo

1. Đăng nhập admin.
2. Chỉ nhanh Users, Departments và Documents.
3. Đăng nhập một member hoặc dùng evidence canary đã khóa.
4. Hỏi một câu và mở citation.
5. Chỉ dòng “tài liệu qua ACL” và title của evidence.
6. Mở Audit nếu còn thời gian.

Nói: “Public preview dùng Supabase RLS nhưng tài khoản admin thật cần user tự
bootstrap. Nếu demo account chưa được tạo, em dùng Docker local hoặc screenshot
canary thay vì nhập credential trên sân khấu.”

## 5:30–6:15 — Slide 10: Verification và giới hạn

“Canonical suite hiện có 63 test pass. Docker image và container health pass.
Public homepage và health endpoint trả HTTP 200. Nhóm từng chạy 20 request local
đều thành công, nhưng đây chỉ là concurrency smoke, không phải cam kết capacity
20 user. Render Free có cold start và public build chưa mang checkpoint lớn.”

## 6:15–7:00 — Slide 11: Kết luận

“Kết quả cho thấy đóng góp khoa học và sản phẩm đã gặp nhau: reranker fine-tuned
cải thiện ranking có đo lường; runtime dùng checkpoint thật; ACL đứng trước
retrieval; web, Docker, Supabase canary và preview tạo thành một MVP có thể demo.
Nhóm không claim full RAGAS, document generalization hoặc production readiness.”

## Nếu demo lỗi

- Public cold start: chuyển sang Docker local.
- Không có admin thật: dùng artifact live canary và screenshot.
- Checkpoint không được mount: nói rõ public đang BM25 fallback; mở integration
  evidence local để chứng minh checkpoint trong runtime.
- Mạng lỗi: trình bày Figma + slide + evidence JSON, không bịa trạng thái live.
