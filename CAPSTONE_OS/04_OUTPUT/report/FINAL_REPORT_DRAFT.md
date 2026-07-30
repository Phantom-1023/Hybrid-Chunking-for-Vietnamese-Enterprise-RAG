# VIETNAMESE ENTERPRISE RAG

## Hybrid Retrieval, Fine-tuned Cross-Encoder và kiểm soát truy cập theo phòng ban

Status: `FINAL REPORT DRAFT / EVIDENCE-LOCKED`

> Bản này là nội dung kỹ thuật chuẩn để đưa vào template báo cáo của trường.
> Các thông tin tên thành viên, giảng viên, mã lớp, hình thức trích dẫn và định
> dạng bìa cần điền theo biểu mẫu chính thức trước khi nộp.

## Tóm tắt

Đồ án xây dựng một hệ thống hỏi đáp tri thức doanh nghiệp bằng tiếng Việt dựa
trên Retrieval-Augmented Generation (RAG). Hệ thống kết hợp Dense Retrieval và
BM25 bằng Reciprocal Rank Fusion (RRF) để lấy 20 đoạn văn ứng viên, sau đó dùng
Cross-Encoder đã fine-tune để chọn 5 bằng chứng phù hợp nhất trước khi tạo câu
trả lời và citation. Song song với chất lượng retrieval, hệ thống áp dụng Access
Control List (ACL) và PostgreSQL Row-Level Security (RLS) trước retrieval nhằm
ngăn tài liệu ngoài quyền đi vào candidate set.

Thực nghiệm dùng 1.141 query tiếng Việt, chia cố định thành 913 train, 114
validation và 114 test với seed 42. Trên cùng locked test và cùng Hybrid RRF
top-20, Cross-Encoder cơ sở đạt MRR 0,779; Cross-Encoder fine-tuned đạt MRR
0,945, Hit@1 0,930 và Hit@5 0,974. Hệ thống có web đa người dùng, quản trị phòng
ban/tài liệu, audit log, Docker runtime, Supabase RLS và public preview. Kết quả
hiện tại đánh giá passage retrieval theo query generalization trên cùng corpus;
không được diễn giải là full RAGAS, document generalization hoặc production
readiness.

**Từ khóa:** Vietnamese RAG, Hybrid Retrieval, BM25, Dense Retrieval,
Cross-Encoder, reranking, ACL, Row-Level Security.

## 1. Giới thiệu

### 1.1 Bối cảnh

Tài liệu doanh nghiệp thường phân tán theo phòng ban, có nhiều thuật ngữ, mã,
tên riêng và cách diễn đạt khác nhau. Một mô hình ngôn ngữ lớn có thể trả lời
trôi chảy nhưng thiếu căn cứ hoặc dùng thông tin ngoài quyền của người hỏi.
RAG giải quyết phần căn cứ bằng cách tìm các đoạn nguồn trước khi sinh câu trả
lời. Tuy nhiên, chất lượng và an toàn của RAG phụ thuộc trực tiếp vào hai câu
hỏi:

1. Hệ thống có đưa đúng passage lên vị trí cao hay không?
2. Hệ thống có loại tài liệu bị cấm trước khi model xử lý hay không?

### 1.2 Mục tiêu

- Xây pipeline retrieval tiếng Việt kết hợp lexical và semantic signals.
- Fine-tune một Cross-Encoder reranker nằm trong query pipeline thật.
- Đánh giá công bằng các phương án trên cùng locked test.
- Xây web MVP có login, role, phòng ban, document scope, admin và audit.
- Áp dụng ACL/RLS trước retrieval và kiểm chứng bằng live canary hai phòng ban.
- Đóng gói Docker và cung cấp public preview có claim boundary rõ ràng.

### 1.3 Đóng góp

1. Pipeline `ACL → Dense + BM25 → RRF top-20 → fine-tuned Cross-Encoder →
   top-5 evidence`.
2. Fine-tuning có split contract, validation checkpoint selection, training
   history, reload test, checksum, before/after metrics và error analysis.
3. Supabase Auth/Postgres RLS adapter giữ user JWT tới database; service key
   không được dùng cho user search.
4. Live canary chứng minh HR và Finance không list/retrieve tài liệu chéo phòng.
5. Web, Docker, Figma, demo, slide và defense pack dùng cùng evidence index.

## 2. Cơ sở lý thuyết

### 2.1 Retrieval-Augmented Generation

RAG gồm hai pha chính. Retrieval tìm các passage liên quan tới query. Generation
dùng passage được chọn làm context để tạo câu trả lời. Đồ án tập trung đo và
cải thiện retrieval/reranking; generation chỉ được claim khi có thí nghiệm
riêng phù hợp.

### 2.2 BM25 và Dense Retrieval

BM25 là thuật toán lexical ranking dựa trên tần suất từ và độ hiếm của từ trong
corpus. BM25 phù hợp với từ khóa chính xác, mã và tên riêng. Dense Retrieval mã
hóa query và passage thành vector, phù hợp với những câu khác cách diễn đạt
nhưng gần nghĩa.

### 2.3 Reciprocal Rank Fusion

RRF hợp nhất các danh sách xếp hạng mà không cần ép score của BM25 và Dense về
cùng thang đo:

```text
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Trong đồ án, hằng số `k = 60` được khóa trước khi xem test.

### 2.4 Cross-Encoder reranker

Cross-Encoder đọc đồng thời cặp `(query, passage)` và trả một relevance score.
Nó thường chính xác hơn bi-encoder nhưng tốn tính toán hơn, vì vậy chỉ dùng để
rerank 20 candidate thay vì toàn bộ corpus. Phần được fine-tune trong đồ án là
Cross-Encoder, không phải BM25 và không phải chatbot LLM.

### 2.5 ACL và Row-Level Security

ACL mô tả user nào được truy cập document nào. RLS thực thi điều kiện này ngay
tại PostgreSQL. Nếu filtering chỉ diễn ra sau retrieval, model vẫn có thể nhận
thông tin bị cấm. Vì vậy thứ tự bắt buộc là:

```text
User identity → SQL/RLS filtering → retrieval → reranking → citation
```

## 3. Phương pháp

### 3.1 Dữ liệu và split

Dataset có 1.141 query. Protocol đánh giá query generalization giữ corpus chung
nhưng tách query thành:

| Split | Số query |
|---|---:|
| Train | 913 |
| Validation | 114 |
| Test | 114 |

Seed được khóa ở 42. Các gate kiểm tra không phát hiện duplicate question hoặc
query-passage pair conflict giữa split. Negative pairs của training chỉ sinh từ
training query.

### 3.2 Baseline

- Dense retrieval.
- BM25 retrieval.
- Hybrid RRF không rerank.
- MMR.
- Base Cross-Encoder.
- Fine-tuned Cross-Encoder.

No-rerank, MMR, base và fine-tuned Cross-Encoder sử dụng cùng Hybrid top-20 và
cùng locked test 114 query.

### 3.3 Fine-tuning contract

Training chạy 2 epoch, tương ứng 572 optimizer step. Checkpoint tốt nhất được
chọn ở epoch 1 theo validation, không chọn bằng test. Quá trình xác minh gồm:

- weights changed check;
- checkpoint reload check;
- training history;
- SHA256 checkpoint;
- locked-test comparison;
- error analysis.

Checksum checkpoint:

```text
3782daf52437af2f2b0bc72a44c128dfa3845eb34b559a1ff8bb1dbcf279aa44
```

Validation MRR bão hòa ở 1,0 cho cả base và fine-tuned. Vì vậy số validation
không được dùng làm bằng chứng cải thiện; kết luận dựa trên locked test và phải
nêu rõ giới hạn dataset.

### 3.4 Metrics

- **MRR:** thưởng cho việc đưa passage đúng lên vị trí đầu.
- **Hit@1 / Hit@5:** tỷ lệ query có positive passage trong top-1/top-5.
- **Recall@20:** khả năng candidate generation giữ positive passage trước
  reranking.

Đây là retrieval metrics, không phải bộ RAGAS đầy đủ cho generation.

## 4. Kiến trúc và triển khai

### 4.1 Research pipeline

```text
Dataset / documents
        ↓
Normalize + locked split
        ↓
BM25 + multilingual Dense Retrieval
        ↓
Hybrid RRF top-20
        ↓
Fine-tuned Cross-Encoder
        ↓
Top-5 evidence
        ↓
Answer + citation
```

Runtime kiểm tra checkpoint checksum trước khi tải model. Integration test xác
nhận live query gọi reranker thật sau khi lấy 20 candidate và chỉ trả 5 evidence.

### 4.2 Web product

FastAPI web MVP hỗ trợ:

- login và session;
- role `admin`, `manager`, `member`;
- department;
- document scope `organization`, `department`, `private`;
- chat/search và citation;
- user/document/department administration;
- audit log.

Local fallback dùng SQLite, PBKDF2 và HMAC-signed session. Managed preview dùng
Supabase Auth, Postgres và RLS.

### 4.3 Supabase security

Migration tạo bốn bảng `departments`, `profiles`, `documents`, `audit_logs` và
bật RLS. Anonymous table grants bị thu hồi. User search chuyển tiếp access token
của chính user tới PostgREST. Audit RPC tự lấy `auth.uid()` thay vì tin actor ID
từ client. Bootstrap admin dùng function có advisory lock.

### 4.4 Docker và deployment

Docker web image đã build và container health pass. Public preview chạy trên
Render Free với Supabase persistence. Homepage và `/api/health` đã đạt HTTP 200
từ bên ngoài. Render Free có thể sleep/cold start; public image không bundle
checkpoint fine-tuned lớn.

## 5. Kết quả

### 5.1 Retrieval baseline

| Phương pháp | MRR |
|---|---:|
| Dense | 0,750 |
| BM25 | 0,660 |
| Hybrid RRF | 0,669 |

Hybrid giữ Recall@20 bằng 1,0, phù hợp vai trò candidate generator cho reranker.

### 5.2 Reranker comparison

| Phương pháp trên cùng Hybrid top-20 | MRR | Hit@1 | Hit@5 |
|---|---:|---:|---:|
| Không rerank | 0,669 | 0,430 | 0,965 |
| MMR | 0,699 | 0,605 | 0,807 |
| Base Cross-Encoder | 0,779 | 0,632 | 0,956 |
| Fine-tuned Cross-Encoder | **0,945** | **0,930** | **0,974** |

Fine-tuned Cross-Encoder tăng MRR từ 0,779 lên 0,945 so với model base trong
cùng điều kiện đánh giá.

### 5.3 Error analysis

So sánh top-5 giữa base và fine-tuned:

| Chuyển trạng thái | Số query |
|---|---:|
| hit → hit | 109 |
| miss → hit | 2 |
| miss → miss | 3 |
| hit → miss | 0 |

Kết quả cho thấy fine-tuning không làm mất các query base đã hit trong tập test,
đồng thời sửa được hai query trước đó miss.

### 5.4 ACL và session privacy

Live canary trên public preview dùng một admin, hai member thuộc HR/Finance và
hai document theo phòng ban. Kết quả:

- HR list/retrieve được HR nhưng không Finance;
- Finance list/retrieve được Finance nhưng không HR;
- member không thấy admin navigation;
- sau khi logout/login user khác trên cùng tab, conversation cũ được xóa;
- toàn bộ dữ liệu canary được dọn sạch và count xác minh về 0.

Canary ban đầu phát hiện frontend giữ conversation cũ sau khi đổi user. Bản vá
`0862b89` thêm reset cho toàn bộ user-scoped UI state; regression canary public
pass. Đây là ví dụ verification thực tế phát hiện lỗi ngoài unit test.

### 5.5 Verification tổng hợp

- Canonical test suite: 63 pass, 1 Pydantic deprecation warning.
- Secret scan: 0 hit.
- Docker build: pass.
- Docker health: healthy.
- Local concurrency smoke: 20/20 HTTP 200, p95 khoảng 1,72 giây.
- Public homepage/health: HTTP 200.

Concurrency smoke là kiểm tra ngắn trên một máy, không phải capacity claim cho
20 user hoạt động bền vững.

## 6. Thảo luận

Fine-tuned Cross-Encoder là đóng góp có giá trị vì nằm đúng bottleneck có thể đo:
passage ranking. Kiến trúc hai tầng giữ candidate generation nhanh và chỉ dùng
Cross-Encoder cho tập nhỏ. ACL-first bảo đảm chất lượng retrieval không đánh đổi
bằng rò rỉ dữ liệu.

Tuy nhiên, validation bão hòa và corpus dùng chung cho thấy dataset chưa đủ để
khẳng định model tổng quát sang tài liệu/domain mới. MRR tăng mạnh cần được hiểu
trong đúng protocol query-generalization đã công bố. Bước đánh giá generation
phải khóa thêm prompt, LLM, judge model và chi phí trước khi dùng RAGAS.

## 7. Giới hạn

- Chưa có full RAGAS cho faithfulness và answer relevancy.
- Chưa chứng minh document-domain generalization.
- Public preview chưa bundle fine-tuned checkpoint lớn.
- Permanent admin đã bootstrap; public login và trang Quản trị đã kiểm chứng.
  Credential không được ghi vào report, artifact, log hoặc Git.
- Render Free có cold start và không đại diện production infrastructure.
- Chưa có load test dài, monitoring, backup/restore drill hoặc penetration test.
- Figma là editable product board, chưa phải componentized production system.

## 8. Hướng phát triển

1. Đưa checkpoint vào hạ tầng có đủ RAM/disk hoặc model registry riêng.
2. Khóa generation experiment và chạy RAGAS trên sample đủ lớn.
3. Bổ sung document/domain split có provenance rõ.
4. Thêm rate limit, observability, backup và incident workflow.
5. Thực hiện load test theo workload thực tế thay vì request smoke.
6. Componentize Figma và đồng bộ design tokens với frontend.

## 9. Kết luận

Đồ án đã triển khai một pipeline RAG tiếng Việt kết hợp Hybrid Retrieval,
fine-tuned Cross-Encoder và ACL-first. Fine-tuned model cải thiện MRR từ 0,779
lên 0,945 trên cùng locked test. Runtime, web đa người dùng, Docker, Supabase RLS
và public preview đều có bằng chứng kiểm chứng tương ứng. Đóng góp chính không
chỉ là một chatbot demo mà là quy trình retrieval/reranking có thể audit, kèm
ranh giới claim minh bạch.

## Phụ lục A — Nguồn bằng chứng

- `CAPSTONE_OS/04_OUTPUT/final/FINAL_EVIDENCE_INDEX.md`
- `artifacts/data/split_manifest.json`
- `artifacts/benchmark/dense_hybrid_baseline.json`
- `artifacts/benchmark/reranker_comparison.json`
- `artifacts/benchmark/reranker_error_analysis.json`
- `artifacts/reranker/full_training_history.csv`
- `artifacts/reranker/full_checkpoint.sha256`
- `artifacts/web/web_smoke.json`
- `artifacts/web/supabase_schema_smoke.json`
- `artifacts/web/supabase_live_canary.json`

## Phụ lục B — Claim boundary bắt buộc

Không gọi kết quả này là full RAGAS, production-ready, sustained 20-user
capacity hoặc document generalization. Mỗi claim cuối phải truy được tới code,
test hoặc artifact trong evidence index.
