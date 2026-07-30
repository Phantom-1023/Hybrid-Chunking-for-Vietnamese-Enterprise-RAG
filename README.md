# Vietnamese Enterprise RAG

Đồ án xây dựng hệ thống hỏi đáp tài liệu doanh nghiệp tiếng Việt có phân quyền,
truy xuất lai (Hybrid Retrieval) và Cross-Encoder đã fine-tune.

## Điểm đóng góp đã kiểm chứng

Pipeline nghiên cứu trên locked test set 114 query:

```text
Dense + BM25 -> Hybrid RRF top-20
             -> fine-tuned Cross-Encoder rerank
             -> top-5 evidence -> citation / LLM
```

| Phương pháp trên cùng candidate set | MRR | Hit@1 | Hit@5 |
|---|---:|---:|---:|
| Không rerank | 0.669 | 0.430 | 0.965 |
| MMR | 0.699 | 0.605 | 0.807 |
| Base Cross-Encoder | 0.779 | 0.632 | 0.956 |
| Fine-tuned Cross-Encoder | **0.945** | **0.930** | **0.974** |

Checkpoint được chọn bằng validation, có training history, error analysis và
SHA256 trong `artifacts/reranker/`. Test tích hợp xác nhận query pipeline thật
lấy top-20 rồi gọi checkpoint fine-tuned để trả top-5.

Giới hạn claim: đây là đánh giá retrieval theo query generalization trên cùng
corpus; không phải full RAGAS, không chứng minh chất lượng generation hay
document generalization.

## Web MVP

Web FastAPI hiện có:

- đăng nhập, one-time admin setup, session có hạn dùng;
- user, role `admin/manager/member`, phòng ban;
- phạm vi tài liệu `organization/department/private`;
- chat, citation, quản lý tài liệu và audit log;
- ACL lọc trong SQL **trước** BM25/reranker.

Integration test chứng minh user Nhân sự không nhìn thấy hoặc retrieve được tài
liệu Tài chính. Mật khẩu được băm PBKDF2-SHA256; không lưu plaintext.

## Chạy nhanh

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-web.txt
$env:WEBAPP_TOKEN_SECRET = "replace-with-a-random-local-secret"
$env:WEBAPP_ENABLE_RERANKER = "true"
$env:RERANKER_CHECKPOINT_PATH = "path-to-local-checkpoint"
.\.venv\Scripts\python.exe -m uvicorn webapp.app:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`. Nếu không có checkpoint, web hạ cấp minh bạch về
ACL-first BM25 và trả tên phương pháp trong `retrieval.method`.

Chạy test:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Kết quả gần nhất: **58 passed**, 1 cảnh báo deprecation từ Pydantic.

## Docker và thiết kế

```powershell
docker build -f docker/Dockerfile.web -t vietnamese-enterprise-rag:web-demo .
docker run --rm -p 8000:8000 vietnamese-enterprise-rag:web-demo
```

- Figma product/architecture board:
  [Vietnamese Enterprise RAG v0.1](https://www.figma.com/design/BmdFhMmjSLzqM6QJqje2ff/Vietnamese-Enterprise-RAG-%C2%B7-Product---Architecture-v0.1?node-id=1-2)
- `render.yaml` là cấu hình preview, chưa phải bằng chứng đã deploy.
- Docker đã build và health-check local; 20 request đồng thời đạt 20/20 HTTP
  200 trên máy thử nghiệm. Đây không phải production capacity claim.

## Nguồn sự thật

- Kế hoạch/chứng cứ: `CAPSTONE_OS/00_CONTEXT/NIGHT_RUN_PLAN.md`
- Product contract: `CAPSTONE_OS/00_CONTEXT/WEB_PRODUCT_CONTRACT.md`
- Gói bảo vệ cuối: `CAPSTONE_OS/04_OUTPUT/final/FINAL_EVIDENCE_INDEX.md`
- Hướng dẫn demo: `CAPSTONE_OS/04_OUTPUT/demo/FINAL_DEMO_SCRIPT.md`
- Hỏi đáp hội đồng: `CAPSTONE_OS/04_OUTPUT/defense/FINAL_DEFENSE_QA.md`

Không commit `.env`, API key, token, mật khẩu, database runtime hoặc checkpoint
weights. Checkpoint được bàn giao riêng và kiểm tra bằng SHA256.
