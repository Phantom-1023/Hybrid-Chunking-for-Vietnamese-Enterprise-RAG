# Phản hồi các điểm yếu trọng yếu

## 1. Vì sao chưa full RAGAS?

Full RAGAS cần thêm dependency/model, thời gian chạy và quota API ổn định hơn. Nhóm không muốn tạo số liệu giả, nên hiện dùng evaluation-lite để có benchmark thật ban đầu. Full RAGAS là bước tiếp theo, không bị claim là đã hoàn thành.

**Evidence:** `K011_EVALUATION_LITE.md`, UI warning, `benchmark_results.csv`.

## 2. Vì sao dùng evaluation-lite?

Evaluation-lite là benchmark proxy nhỏ, chạy nhanh và đo trực tiếp từ pipeline hiện tại. Nó cho thấy hệ thống đã có khả năng đo retrieval behavior thật thay vì chỉ demo cảm tính. Nó không thay thế RAGAS.

**Câu nói an toàn:** "Evaluation-lite là bước kiểm tra MVP, không phải kết luận học thuật cuối cùng."

## 3. Vì sao chỉ 5 samples?

Vì mục tiêu hiện tại là demo ổn định trong thời gian ngắn, tránh quota/API và tránh làm máy lag. 5 samples đủ để có tín hiệu thật cho MVP, nhưng chưa đủ cho kết luận tổng quát. Nhóm sẽ tăng sample khi chạy full evaluation.

**Không nói:** "5 mẫu là đủ đại diện toàn bộ dataset."

## 4. Vì sao dùng `gemini-embedding-001` thay vì `text-embedding-004`?

API key hiện tại không hỗ trợ `text-embedding-004`, nên nhóm dùng execution patch `gemini-embedding-001` để MVP chạy được. Mission gốc không bị đổi; patch này được ghi rõ trong UI và tài liệu.

**Không nói:** "Nhóm tự ý đổi model trong mission."

## 5. Vì sao semantic chunking fallback?

Semantic chunking có thể nặng hoặc phụ thuộc runtime/model. Để đảm bảo demo không crash, strategy semantic vẫn tồn tại nhưng có fallback. Nhóm minh bạch điểm này và không claim semantic hiện là bản đầy đủ.

**Câu nói an toàn:** "Fallback là quyết định demo-safety, không phải kết quả nghiên cứu cuối."

## 6. Vì sao chưa upload file doanh nghiệp?

Upload file doanh nghiệp nằm ngoài MVP hiện tại. Review 1 yêu cầu dataset không phụ thuộc doanh nghiệp, nên nhóm ưu tiên dataset public có ground truth để benchmark. Upload doanh nghiệp là phase mở rộng sau khi benchmark lõi ổn định.

**Không nói:** "Upload file đã có nhưng chưa bật."

## 7. Vì sao gọi là Enterprise RAG?

Vì hướng bài toán là quản lý tri thức doanh nghiệp: tài liệu nội bộ, quy trình, chính sách, báo cáo. MVP hiện làm lõi kỹ thuật của Enterprise RAG: retrieval, source transparency, strategy comparison. Production features như phân quyền/audit/upload nằm ở phase sau.

**Không nói:** "Hệ thống đã sẵn sàng production."

## 8. Vì sao paragraph strategy thắng bây giờ?

Trong evaluation-lite trên 5 mẫu, paragraph có `avg_score = 0.8354`, cao nhất. Lý do hợp lý là context của dataset có cấu trúc đoạn phù hợp, nên chia theo paragraph giữ được ngữ cảnh tốt hơn. Nhưng đây chỉ là tín hiệu ban đầu, chưa phải kết luận full RAGAS.

**Evidence:** `benchmark_results.csv`.

## 9. Benchmark hiện tại có đủ không?

Đủ để chứng minh MVP có benchmark thật và UI hiển thị số thật, nhưng chưa đủ để kết luận khoa học cuối cùng. Để đủ cho báo cáo cuối, nhóm cần full RAGAS và sample lớn hơn.

**Câu nói an toàn:** "Đủ cho demo MVP, chưa đủ cho kết luận nghiên cứu cuối."

## 10. Cải tiến khoa học tiếp theo là gì?

Chạy full RAGAS với 4 metrics: Faithfulness, Answer Relevancy, Context Recall, Context Precision. Sau đó tăng sample, so sánh strategy bằng thống kê rõ ràng, và phân tích lỗi theo loại câu hỏi/context.

**Không nói:** "Chỉ cần thêm UI là xong nghiên cứu."
