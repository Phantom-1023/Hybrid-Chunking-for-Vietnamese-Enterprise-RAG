# FINAL EVIDENCE INDEX

Status: `VERIFIED LOCAL MVP / NOT PRODUCTION-DEPLOYED`

## Một câu mô tả đồ án

Hệ thống RAG tiếng Việt cho doanh nghiệp, trong đó ACL lọc tài liệu trước truy
xuất; Dense và BM25 tạo top-20; Cross-Encoder đã fine-tune rerank thành top-5
evidence có citation.

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
| Error analysis | 109 hit→hit, 2 miss→hit, 3 miss→miss | `artifacts/benchmark/reranker_error_analysis.json` |
| ACL trước retrieval | cross-department denial pass | `tests/test_webapp_acl.py` |
| Web + Docker | 58 tests; Docker healthy | `artifacts/web/web_smoke.json` |
| Supabase schema/RLS | 4 bảng bật RLS; 10 policy | `artifacts/web/supabase_schema_smoke.json` |
| Thiết kế | editable Figma product board | `artifacts/design/figma_delivery.json` |

## Không được nói quá

- Không gọi benchmark này là full RAGAS.
- Không nói đã chứng minh document generalization.
- Không nói production-ready hoặc phục vụ bền vững 20 user.
- Không nói đã deploy public khi chưa có URL và smoke test từ bên ngoài.
- Không commit checkpoint weights hay secrets.

## Definition of Done hiện tại

- Research core: pass.
- Runtime reranker integration: pass.
- Web auth/role/department/document ACL: pass local.
- Docker package và local health: pass.
- Figma product board: pass v0.
- Supabase schema/RLS: pass; web Auth/Postgres integration còn pending.
- Public deployment: pending URL và external smoke test.
- Báo cáo/slide chính thức: cần đồng bộ nội dung từ evidence index này.
