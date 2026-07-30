# MISSION CONTRACT v0.2

Status: `APPROVED / ACTIVE`

## 1. Mission

Hoàn thiện một MVP RAG tiếng Việt cho tri thức doanh nghiệp có thể bảo vệ trước
hội đồng:

```text
ACL theo user/phòng ban
        ↓
Dense + BM25
        ↓
Hybrid RRF lấy top-20
        ↓
Fine-tuned Cross-Encoder rerank
        ↓
Top-5 evidence + citation
        ↓
LLM hoặc fallback không bịa
```

Đóng góp fine-tune bắt buộc nằm trong query pipeline thật. BM25 là lexical
retrieval baseline, không phải mô hình được fine-tune.

## 2. Scientific contract

- Dùng cùng locked test set cho no-rerank, MMR, base Cross-Encoder và
  fine-tuned Cross-Encoder.
- Checkpoint chọn bằng validation, không chọn bằng test.
- Bằng chứng bắt buộc: split/leakage report, pair manifest, training history,
  checkpoint reload, checksum, before/after metrics và error analysis.
- Phạm vi kết luận hiện tại là query generalization trên cùng corpus.
- Không gọi benchmark retrieval này là full RAGAS.
- Không giả số, không chọn lại protocol sau khi nhìn test.

## 3. Product contract

- Web có login, user, role, phòng ban, document scope, admin và audit.
- ACL/RLS lọc document trước retrieval và reranking.
- Same-browser logout/login phải xóa toàn bộ state theo user trước.
- Docker phải chạy local và public preview phải có health check bên ngoài.
- Figma là product/architecture board editable; chưa claim design system hoàn chỉnh.

## 4. Definition of Done

1. Research pipeline và fine-tuned checkpoint có evidence audit được.
2. Runtime thật chạy top-20 → rerank → top-5 evidence.
3. Auth/ACL/admin chạy local; Supabase RLS có live two-department canary.
4. Docker healthy và có temporary public preview.
5. README, evidence index, demo script, report outline, slide và defense Q&A
   dùng cùng bảng số liệu khóa.
6. Secrets, private data và checkpoint weights lớn không vào Git.
7. Mọi giới hạn còn lại được ghi rõ thay vì overclaim.

## 5. Git and autonomy

- Chỉ làm và push lên `review2-mvp-demo`; không push/merge trực tiếp `main`.
- Không stage toàn bộ dirty worktree.
- Loop tự chủ: `inspect → implement one slice → verify → evidence → commit → push`.
- Agent tự xử lý trong contract sau một lần duyệt; user chỉ giữ quyết định có
  đòn bẩy lớn.
- Hard stop: nguy cơ mất dữ liệu, lộ secret, phát sinh chi phí, sai nhánh hoặc
  thay Mission Contract.

## 6. Claim boundary

Được nói:

- Fine-tuned reranker cải thiện retrieval MRR trên locked test.
- ACL-first retrieval đã pass local test và bounded live Supabase canary.
- Docker và Render Free public preview đã được smoke-test.

Không được nói:

- Full RAGAS đã hoàn tất.
- Production-ready hoặc phục vụ bền vững 20 user.
- Document-domain generalization đã được chứng minh.
- Figma đã là production design system.

## 7. Canonical control set

Chỉ cần mở các nguồn sau:

1. `CAPSTONE_OS/00_CONTEXT/NIGHT_RUN_PLAN.md`
2. `CAPSTONE_OS/04_OUTPUT/final/FINAL_EVIDENCE_INDEX.md`
3. `CAPSTONE_OS/04_OUTPUT/report/FINAL_REPORT_DRAFT.md`
4. `CAPSTONE_OS/04_OUTPUT/demo/FINAL_DEMO_SCRIPT.md`
5. `CAPSTONE_OS/04_OUTPUT/defense/ONE_PAGE_LAST_MINUTE_REVIEW.md`

Các README/STATE/PROGRESS hoặc benchmark lịch sử không được dùng làm claim nếu
chưa đối chiếu với evidence index.

## 8. Human gate đã hoàn tất

Public preview đã pass health và live canary bằng tài khoản tạm; toàn bộ dữ liệu
tạm đã được dọn sạch. Permanent admin đã bootstrap riêng và public login/trang
Quản trị đều pass. Credential không được ghi vào file, artifact, log hoặc Git.
