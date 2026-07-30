# Data Split Contract — chống leakage trước khi fine-tune

**Trạng thái:** Protocol A đã được adopt trong Night Run; chưa tạo split và chưa train.

## Vì sao cần file này?

Dataset có 1.141 record và mỗi record chứa 5 context passage. Câu hỏi, đáp án và
toàn bộ context ghép theo record không trùng chính xác, nhưng nhiều passage riêng
lẻ được tái sử dụng giữa các record.

Nếu chia ngẫu nhiên từng record hoặc từng chunk, cùng một passage có thể xuất
hiện ở cả train và test. Khi đó reranker có thể đã nhìn thấy ngữ cảnh test trong
lúc train, làm kết quả before/after cao giả tạo.

## Kết quả audit ảnh hưởng trực tiếp tới cách split

- 1.141 question, answer và joined-context đều không trùng chính xác.
- 5.705 context passage chứa 4.641 passage duy nhất.
- Có 1.064 lượt passage lặp ngoài bản đầu tiên, thuộc 899 nhóm duplicate.
- Nếu nối hai record khi chúng dùng chung bất kỳ passage nào, ta chỉ còn 169
  connected group; group lớn nhất chứa 883/1.141 record.

Vì vậy **không được áp dụng máy móc group split theo toàn bộ 5 context**: nó
không thể tạo các split cân bằng và có thể đang nối record qua distractor dùng
chung, không phải positive passage.

## Luật bắt buộc

1. Chia dữ liệu ở cấp **record gốc**, trước khi chunking.
2. Không để cùng question hoặc cùng query-passage training pair xuất hiện ở
   nhiều split.
3. Chỉ fit model trên train.
4. Dùng dev để chọn checkpoint, threshold và hyperparameter.
5. Không nhìn test để điều chỉnh model; test chỉ chạy sau khi khóa lựa chọn.
6. Chunk/query-passage pair tạo từ một record phải kế thừa split của query.
7. Hard negative phục vụ train chỉ được sinh từ train query.
8. Lưu seed, thuật toán split, ID record và hash snapshot vào artifact.
9. Baseline và fine-tuned model phải chạy trên đúng cùng test set.
10. Report phải nói rõ protocol nào dưới đây được sử dụng.

## Protocol được adopt

### A. Query generalization trên cùng corpus

- Train/dev/test chứa các question khác nhau.
- Retrieval corpus có thể dùng chung giữa các split.
- Đo khả năng trả lời câu hỏi mới trên cùng kho tài liệu doanh nghiệp.
- Khả thi với dataset và deadline hiện tại.

**Quyết định Night Run:** dùng Protocol A với tỷ lệ `80/10/10`, seed `42`.
Claim được phép chỉ là tổng quát sang câu hỏi mới trên cùng corpus; không claim
document generalization.

### B. Passage/document generalization nghiêm ngặt

- Test phải dùng tài liệu hoặc positive passage chưa xuất hiện ở train.
- Đo khả năng chuyển sang tài liệu mới.
- Dataset hiện không có source/document ID hoặc nhãn positive-passage rõ ràng;
  cần thêm bước suy luận/ghi nhãn và kiểm chứng thủ công.
- Có rủi ro lớn hơn về thời gian và độ đúng.

## Label và negative-sampling gate

- Không được mặc định `context[0]` là positive chỉ vì vị trí của nó.
- Chạy `scripts/audit_positive_labels.py` và audit semantic mẫu trước khi sinh pair.
- Exact-answer containment là evidence chắc nhưng không bao phủ mọi paraphrase.
- Answer-token recall chỉ là tín hiệu chọn mẫu audit, không tự biến thành nhãn.
- Nếu audit không bảo vệ được `context[0]`, chuyển sang multiple-positive hoặc
  annotation contract; không silent fallback.
- Số negative/query được khóa sau khi first-stage candidate pool P1 đã pass.
- Hard negative của train chỉ lấy từ train query; dev/test không được dùng để mine.

**Kết quả Night Run:** gate đã pass. Aggregate audit cho thấy context 0 có
answer-token recall tốt nhất ở 1.139/1.141 record. Semantic audit deterministic
50 record, seed 42, kết luận 50 `context0_positive`, 0 ambiguous và 0 fail.

Label contract được adopt:

- `context[0]` là primary positive passage ở passage level.
- Chunk phải giữ `source_passage_index`; positive chunk sinh từ passage 0.
- Context 1–4 chỉ là negative candidate sau deduplicate.
- Nếu phát hiện context khác cũng trực tiếp hỗ trợ answer, row đó chuyển thành
  multiple-positive và context ấy không được dùng làm negative.

Các quyết định trên được adopt theo `NIGHT_RUN_PLAN.md`. Mọi manifest phải lưu
protocol, tỷ lệ, seed, label contract và snapshot hash trước khi training.
