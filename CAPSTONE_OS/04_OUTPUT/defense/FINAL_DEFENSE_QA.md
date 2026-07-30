# FINAL DEFENSE Q&A

Status: `CANONICAL DEFENSE TRAINING`

## 1. Fine-tune cái gì?

Fine-tune Cross-Encoder reranker, không fine-tune BM25. BM25 là thuật toán xếp
hạng từ khóa không có neural weights theo cách này. Model nhận cặp
`(query, passage)` và học chấm điểm passage liên quan.

## 2. Vì sao chưa fine-tune LLM?

Nút thắt được đo ở retrieval/ranking và yêu cầu đồ án cần fine-tune có bằng
chứng. Fine-tune reranker vừa nằm đúng pipeline, vừa đánh giá before/after rõ,
ít dữ liệu và tài nguyên hơn fine-tune LLM.

## 3. Baseline và pipeline khác gì?

Pipeline là toàn bộ luồng xử lý. Baseline là phương án mốc để so sánh trong một
đoạn của pipeline. Ở đây no-rerank, MMR và base Cross-Encoder là baseline;
fine-tuned Cross-Encoder là phương án đề xuất.

## 4. Vì sao cần cả BM25 và Dense?

BM25 mạnh với từ khóa chính xác, mã và tên riêng. Dense mạnh với câu diễn đạt
khác nhưng cùng nghĩa. RRF kết hợp thứ hạng mà không cần ép hai loại score về
cùng thang đo.

## 5. Vì sao retrieval top-20 rồi mới rerank?

Retriever nhanh tạo một tập ứng viên đủ rộng. Cross-Encoder chính xác hơn nhưng
tốn tính toán, nên chỉ chấm 20 ứng viên và trả 5 evidence.

## 6. Làm sao biết model fine-tuned tốt hơn?

So trên cùng locked test và cùng candidate set: base MRR 0.779, fine-tuned MRR
0.945. Checkpoint chọn bằng validation; test chỉ dùng báo cáo cuối.

## 7. Có leakage không?

Contract tách theo query, kiểm tra duplicate query/pair giữa split và khóa seed.
Phạm vi hiện tại là query generalization trên cùng corpus, chưa claim document
generalization.

## 8. Validation đều 1.0 có đáng ngờ không?

Có. Tập validation nội-record dễ và bão hòa cho cả base lẫn fine-tuned, nên
không dùng nó để claim cải thiện. Nó chỉ dùng checkpoint selection; kết luận
dựa trên locked query-generalization test và phải nêu giới hạn này.

## 9. ACL có thực sự an toàn?

Trong MVP, SQL lọc tài liệu theo user/role/department trước retrieval. Test
cross-department và reranker spy xác nhận model chưa từng nhận tài liệu bị cấm.
Production vẫn cần Postgres RLS, secret management và security review.

## 10. Đây đã là production chưa?

Chưa. Đây là local/Docker MVP có health và concurrency smoke. Chưa có public
deployment, persistent managed database, monitoring, backup, rate limit và
security audit production.

## 11. Có phải RAGAS không?

Không. Hiện có retrieval metrics MRR/Hit@k/Recall và error analysis. RAGAS cho
faithfulness/answer relevancy là bước tiếp theo khi có generation experiment
được khóa và chi phí đánh giá phù hợp.

## 12. Nếu hội đồng chỉ hỏi đóng góp mới?

“Nhóm đưa fine-tuned Vietnamese reranker vào query pipeline thật, chứng minh
before/after trên locked test, đồng thời thiết kế ACL-first để dữ liệu ngoài
quyền không bao giờ đi vào retriever/reranker.”
