# V1.0.5 — Baseline canonical

Ngày kiểm tra: 13/08/2026. Tài liệu này ghi nhận baseline trước khi thực hiện bất kỳ cải tiến product nào.

## 1. Base SHA và nhánh

- Product base bắt buộc: `58df599650c919391698b24b3ac0e5aefffbeb42`.
- Nhánh canonical mới: `final/v1.0.5`.
- HEAD của worktree audit sau khi tạo nhánh: `58df599650c919391698b24b3ac0e5aefffbeb42`.
- `git merge-base final/v1.0.5 58df599650c919391698b24b3ac0e5aefffbeb42` trả về `58df599650c919391698b24b3ac0e5aefffbeb42`.

Nhánh được tạo trực tiếp từ SHA base, không merge và không cherry-pick toàn bộ evidence branch.

## 2. Quan hệ với v1.0.4 và evidence branch

- `origin/release/v1.0.4` và `origin/review2-mvp-demo` đều trỏ tới cùng SHA `58df599` tại thời điểm kiểm tra.
- Vì vậy baseline product của `final/v1.0.5` có cùng hành vi product source với v1.0.4 trước thay đổi mới.
- `final-evidence-20260813@8b040fa793557043d134c35ea92600ccafa2612e` là hậu duệ của cùng base nhưng là nhánh evidence/report, không phải product baseline.
- Không có runtime/product source nào từ evidence branch được copy sang nhánh này.

## 3. Baseline test trước thay đổi

Lệnh chạy từ worktree `final/v1.0.5`, dùng môi trường đã tồn tại và pytest temp nằm trong worktree:

```powershell
C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .\P0_RELEASE\pytest-baseline-v1.0.5
```

Kết quả: **`80 passed, 2 warnings in 19.21s`**; wall-clock `20.69s`; exit code `0`.

Hai warning là Pydantic class-based config deprecation và Starlette multipart pending-deprecation. Không có assertion failure. Con số 80 là baseline trước khi giữ test dài bên dưới.

## 4. Review chọn lọc evidence branch

Diff được review: `58df599..8b040fa`.

| Candidate từ evidence branch | Quyết định | Lý do |
|---|---|---|
| `tests/test_long_document_acceptance.py` | `KEEP_IN_FINAL_PRODUCT` | Test synthetic, xác nhận ingestion TXT dài, thứ tự chunk, truy hồi BM25 fact đầu/giữa/cuối và chặn upload vượt 15 MiB. Không đổi runtime, benchmark hoặc claim khoa học. |
| `P0_CONTROL/**` (6 file) | `KEEP_AS_EXTERNAL_EVIDENCE` | Traceability/release QA cho báo cáo, không thuộc product runtime. |
| `P0_HANDOFF/**` (3 file) | `KEEP_AS_EXTERNAL_EVIDENCE` | Handoff và lịch sử P0, không thuộc product runtime. |
| `P0_RELEASE/AIP491_CAPSTONE_REPORT_REVISED_2026-08-13.docx` và các Markdown release/evidence | `KEEP_AS_EXTERNAL_EVIDENCE` | Artifact báo cáo/bằng chứng; không đưa DOCX hay claim vào source product. |
| `P0_WORK/admin_metadata*.json`, `artifact.md`, `report_content.md` | `KEEP_AS_EXTERNAL_EVIDENCE` | Dữ liệu làm report/control, không dùng bởi product runtime. |
| `scripts/build_p0_aip491_report.py` | `DROP_FROM_PRODUCT_BRANCH` | Chỉ là report builder; không phải runtime, test hoặc deployment của product. |

Chỉ file test được giữ. Không có chỉnh sửa kiến trúc, dependency, benchmark artifact, retraining, source retrieval hay UI trong bước chọn lọc này.

## 5. Kết quả test sau khi giữ test dài

Test được chạy riêng để không lẫn với baseline:

```powershell
C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_long_document_acceptance.py
```

Kết quả: **`2 passed, 1 warning in 0.16s`**; wall-clock `0.73s`; exit code `0`.

Sau đó toàn suite được chạy lại:

```powershell
C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .\P0_RELEASE\pytest-with-long-acceptance-v1.0.5
```

Kết quả: **`82 passed, 2 warnings in 19.01s`**; wall-clock `20.64s`; exit code `0`.

Đây là coverage chức năng bounded: nó không chứng minh document/domain generalization, neural retrieval, generation quality, RAGAS hay production performance.

## 6. Known limitations tại baseline

- `render.yaml` đặt `WEBAPP_ENABLE_HYBRID_RETRIEVAL=false` và `WEBAPP_ENABLE_RERANKER=false`; cấu hình public demo là lightweight demo path, không phải xác nhận runtime Hybrid + fine-tuned Cross-Encoder.
- Checkpoint fine-tuned không được bundle trong Git; không re-download, retrain hoặc tự nhận đã xác minh full local research runtime trong task này.
- Loader không triển khai OCR cho PDF scan/image-only; khả năng DOCX/XLSX/CSV/TXT có test bounded riêng, không phải chứng minh mọi loại tài liệu.
- Pydantic và Starlette vẫn phát warning deprecation trong test suite.
- Audit UI trong task này là audit source/static có kiểm chứng. Không có local visual run-through: việc khởi chạy server local đã bị lớp quyền thực thi từ chối trước khi tiến trình được tạo; không thử lại bằng workaround.
- Tài liệu legacy có drift: `README.md` còn ghi mốc `63 passed`, `CAPSTONE_OS/00_CONTEXT/CURRENT_STATE.md` mô tả mission/stack cũ, trong khi baseline test hiện tại là 80 trước test dài.

## 7. Current public demo mode

Theo `render.yaml` và product contract trong repository, demo public dùng FastAPI với Supabase backend/RLS và Render health check, nhưng tắt Hybrid retrieval và reranker trong cấu hình deploy. Task này không deploy và không thực hiện live probe mới; vì vậy đây là mô tả cấu hình repository, không phải xác nhận runtime public mới tại thời điểm xuất tài liệu.

## 8. Phạm vi không làm trong task này

Không redesign UI, không implement backlog, không thay product source ngoài test coverage được phép, không merge evidence branch, không deploy và không thay đổi benchmark/claim khoa học.
