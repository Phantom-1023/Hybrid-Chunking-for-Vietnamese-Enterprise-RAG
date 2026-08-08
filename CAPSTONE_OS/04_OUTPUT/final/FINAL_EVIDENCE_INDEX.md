# FINAL EVIDENCE INDEX

Status: `VERIFIED MVP + PUBLIC PREVIEW / NOT PRODUCTION-READY`

## Sự thật hiện tại (ưu tiên hơn tài liệu cũ)

| Mức | Trạng thái đã kiểm chứng |
|---|---|
| Tracked code | Hybrid nằm sau cờ `WEBAPP_ENABLE_HYBRID_RETRIEVAL=false`; mặc định giữ nguyên BM25. |
| Local test | ACL chạy trước cả BM25/Dense; RRF `k=60`; chỉ fused candidates vào reranker; citation và fallback đều có test. |
| Public Render | Bằng chứng smoke hiện có chỉ gắn với commit cũ `0862b89`; cấu hình public hiện vẫn là BM25, chưa chứng minh Hybrid/FT CE đã deploy. |
| Chưa có bằng chứng | Đóng góp **Hybrid Chunking**, đánh giá Việt-Anh, RAGAS, document-generalization và production readiness. |

## Một câu mô tả đồ án

Hệ thống RAG tiếng Việt có ACL-first và citation. Runtime mặc định dùng BM25;
prototype Hybrid tùy chọn dùng BM25 top-20 + Dense top-20 -> RRF ->
fine-tuned Cross-Encoder -> top-5, và tự fallback về BM25 khi lỗi.

## Bằng chứng bắt buộc

| Claim | Kết quả | Nguồn |
|---|---|---|
| Split không trùng query/pair | 913/114/114, seed 42 | `artifacts/data/split_manifest.json`, `leakage_report.json` |
| Baseline cùng locked test | Dense 0.750; BM25 0.660; Hybrid 0.669 MRR | `artifacts/benchmark/dense_hybrid_baseline.json` |
| Fine-tune chạy thật | 2 epochs, 572 steps, weights changed | `artifacts/reranker/full_result.json` |
| Chọn checkpoint đúng | validation-based, epoch 1 | `artifacts/reranker/full_training_history.csv` |
| Checkpoint toàn vẹn | SHA256 `3782daf...aa44` | `artifacts/reranker/full_checkpoint.sha256` |
| Reranker nằm trong runtime | top-20 -> FT CE -> top-5 | `src/retriever.py`, integration test |
| Cải thiện locked test | base 0.779 -> FT 0.945 MRR | `artifacts/benchmark/reranker_comparison.json` |
| Độ chắc chắn của cải thiện | FT-base: Delta Hit@1 0.298, CI95% [0.219, 0.386]; Delta MRR@5 0.168, CI95% [0.119, 0.218] | `artifacts/benchmark/reranker_statistics.json` |
| Error analysis | 109 hit→hit, 2 miss→hit, 3 miss→miss | `artifacts/benchmark/reranker_error_analysis.json` |
| ACL trước retrieval | cross-department denial pass | `tests/test_webapp_acl.py` |
| Web + Docker | Bằng chứng lịch sử: 63 tests; Docker healthy | `artifacts/web/web_smoke.json` |
| Public preview | Bằng chứng lịch sử ở `0862b89`: Render HTTP 200 + Supabase health | `artifacts/web/web_smoke.json` |
| Supabase schema/RLS | 4 bảng bật RLS; 9 policy; audit RPC | `artifacts/web/supabase_schema_smoke.json` |
| Supabase live canary | HR ↔ Finance denial; session-switch privacy pass | `artifacts/web/supabase_live_canary.json` |
| Permanent admin | bootstrap + public login + admin page pass | `artifacts/web/permanent_admin_smoke.json` |
| Thiết kế | editable Figma product board | `artifacts/design/figma_delivery.json` |
| Slide bảo vệ | 11 slide, render/overflow QA pass | `CAPSTONE_OS/04_OUTPUT/slides/RAG_ENTERPRISE_FINAL_DEFENSE.pptx` |
| Báo cáo kỹ thuật | final draft đồng bộ evidence/limitations | `CAPSTONE_OS/04_OUTPUT/report/FINAL_REPORT_DRAFT.md`, `VIETNAMESE_ENTERPRISE_RAG_FINAL_REPORT.docx` |

## Không được nói quá

- Không gọi benchmark này là full RAGAS.
- Không nói đã chứng minh document generalization.
- Không nói production-ready hoặc phục vụ bền vững 20 user.
- Không nói đã deploy public khi chưa có URL và smoke test từ bên ngoài.
- Không commit checkpoint weights hay secrets.

## Definition of Done hiện tại

- Research core: pass.
- Runtime Hybrid + reranker integration: pass local sau feature flag; chưa chứng minh trên Render.
- Web auth/role/department/document ACL: pass local.
- Docker package và local health: pass.
- Figma product board: pass v0.
- Supabase schema/RLS + runtime adapter + live two-user RLS canary: pass.
- Same-browser logout/login privacy: pass sau bản vá `0862b89`.
- Public preview: smoke lịch sử pass; chưa có revision endpoint để gắn public runtime với HEAD mới.
- Slide chính thức và final report Markdown/DOCX: pass; cùng dùng evidence index
  làm bảng số liệu khóa.

## Năm câu defense cần nhớ

1. **Vì sao BM25 + Dense?** BM25 bắt từ khóa chính xác; Dense bắt tương đồng ngữ nghĩa. Hai tín hiệu bổ sung nhau.
2. **Vì sao RRF?** RRF hợp nhất thứ hạng mà không cần chuẩn hóa hai thang điểm khác nhau; `k=60` được khóa để so sánh công bằng.
3. **Hybrid có tốt hơn Dense không?** Không ở Hit@1 trên locked test. Giá trị của nó là giữ Recall@20 = 1.0 và tạo candidate pool ổn định cho reranker.
4. **Fine-tune tạo khác biệt gì?** Trên cùng 114 query/candidate pool, Hit@1 tăng từ 0.632 lên 0.930 so với base CE; CI paired bootstrap không chứa 0.
5. **Vì sao chưa production-ready?** Chỉ có offline same-corpus evaluation và local integration tests; chưa có tải 20 user, monitoring, mixed-language, RAGAS hay deploy Hybrid/FT CE được xác nhận.
