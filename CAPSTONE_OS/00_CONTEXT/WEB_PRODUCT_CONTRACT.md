# WEB PRODUCT CONTRACT

Status: `PUBLIC DEMO DEPLOYED / PERMANENT ADMIN VERIFIED`

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

- FastAPI có hai backend: SQLite local fallback và Supabase Auth/Postgres RLS.
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
- Render Free preview đã deploy đúng nhánh `review2-mvp-demo`; homepage và
  `/api/health` đều HTTP 200. Free instance có thể sleep.
- Supabase project đã healthy; migration tạo `departments`, `profiles`,
  `documents`, `audit_logs` và bật RLS đã chạy pass. Truy vấn kiểm chứng trả đủ
  4 bảng với 2/2/4/1 policy.
- Supabase runtime adapter dùng user access token cho mọi PostgREST read/write;
  service-role chỉ dành cho bootstrap/admin server-side.
- HTTP bootstrap mặc định đóng; chỉ mở khi có one-time bootstrap proof, và RPC
  dùng advisory lock bảo đảm chỉ một admin đầu tiên thắng.
- Audit event đi qua RPC tự lấy `auth.uid()`; authenticated user không có quyền
  insert trực tiếp để giả actor.
- Mock-transport integration test chứng minh user bearer đi vào PostgREST/RLS
  trước khi candidate được chuyển cho reranker. Permanent admin login và
  authorization đã pass trên public preview; chưa claim end-to-end production.
- `render.yaml` dùng Supabase backend và yêu cầu secret qua dashboard; không đưa
  password/key vào file hoặc Git.
- Chưa claim production readiness hoặc 20-user sustained capacity. Public
  preview chưa bundle fine-tuned checkpoint do giới hạn tài nguyên deploy free.
