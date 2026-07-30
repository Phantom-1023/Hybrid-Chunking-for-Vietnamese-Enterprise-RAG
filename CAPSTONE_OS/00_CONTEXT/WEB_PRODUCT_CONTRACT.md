# WEB PRODUCT CONTRACT

Status: `IMPLEMENTED LOCAL DEMO / DEPLOYMENT NOT YET CLAIMED`

## Product boundary

- Web là product shell chính; Streamlit cũ được giữ làm research/demo fallback.
- Luồng người dùng: login -> hỏi đáp -> xem citation -> xem tài liệu được phép.
- Luồng quản trị: phòng ban -> user/role -> document scope -> audit log.
- Vai trò MVP: `admin`, `manager`, `member`.
- Phạm vi tài liệu: `organization`, `department`, `private`.

## Security invariant

ACL phải lọc tập tài liệu trong SQL trước BM25/dense/reranker. Không được retrieve
toàn bộ rồi mới ẩn citation ở UI. Integration test bắt buộc chứng minh user Nhân sự
không nhận tài liệu Tài chính dù câu hỏi khớp mạnh với nội dung Tài chính.

## Current implementation

- FastAPI + SQLite demo persistence.
- Password: salted PBKDF2-SHA256; signed expiring session.
- One-time admin setup; admin quản lý phòng ban/user; manager thêm tài liệu đúng
  phòng ban; member chỉ đọc/hỏi.
- Search web shell: ACL-first SQL filter -> BM25 top-20 -> fine-tuned
  Cross-Encoder -> top-5 citation khi `WEBAPP_ENABLE_RERANKER=true`.
- Integration test dùng reranker spy chứng minh nó chỉ nhận tài liệu đã qua ACL.
- Chế độ container nhẹ có thể tắt model và hạ xuống ACL-first BM25; response luôn
  công bố `retrieval.method`, không giả vờ đã dùng fine-tuned model.

## Deployment boundary

- `docker/Dockerfile.web` là image demo tối giản.
- `render.yaml` là cấu hình preview; free instance có thể sleep và filesystem có
  thể không bền.
- Supabase project đã healthy; migration tạo `departments`, `profiles`,
  `documents`, `audit_logs` và bật RLS đã chạy pass. Truy vấn kiểm chứng trả đủ
  4 bảng với 2/2/4/2 policy.
- Web runtime hiện vẫn dùng SQLite. Chưa claim Supabase integration cho tới khi
  Auth/Postgres end-to-end test pass; không đưa password/key vào file hoặc Git.
- Chưa claim production readiness, 20-user capacity hoặc deployed URL trước khi
  có smoke/load evidence thật.
