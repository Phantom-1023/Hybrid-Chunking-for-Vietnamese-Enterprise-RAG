# Sprint 1 QA — v1.0.5

## Revisions

- Starting SHA: `69dc58d1cc7eb80ffb53afb8ad52f77cb21fbda1`
- Ending implementation SHA: `fb55726b6204fcfd5f09da2a68fbba80bf173e1f`
- Base product ancestry: `58df599650c919391698b24b3ac0e5aefffbeb42 -> 69dc58d -> fb55726`

## Commands and results

| Scope | Exact command | Result |
|---|---|---|
| JavaScript syntax | `node --check webapp\static\app.js` | Exit `0`. |
| Focused frontend/ACL regression | `C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_webapp_frontend_privacy.py tests\test_webapp_frontend_polish.py tests\test_webapp_product_hardening.py tests\test_webapp_acl.py --basetemp .\P0_RELEASE\pytest-sprint1-focused` | `15 passed, 2 warnings in 6.56s`. |
| Full suite | `C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .\P0_RELEASE\pytest-sprint1-full` | `84 passed, 2 warnings in 15.54s`; wall-clock `16.86s`; exit `0`. |

Warnings là Pydantic class-based config deprecation và Starlette multipart pending-deprecation. Không có test failure.

## ACL regression status

PASS trong focused suite. `tests/test_webapp_acl.py` và `tests/test_webapp_product_hardening.py` cùng chạy pass; Sprint 1 không sửa endpoint authorization, ACL-first retrieval hoặc persistence/migration.

## Visual QA status

**NOT PASSED / NOT CLAIMED.** Lần khởi chạy local server trước visual audit bị lớp quyền thực thi từ chối trước khi tiến trình được tạo. Theo quy tắc task, không thử workaround hay giả nhận visual QA.

Manual checks còn phải làm khi có thể chạy local/browser an toàn:

1. Login: pending label, double-submit prevention, login error.
2. Chat: welcome, pending label, citation result, no-evidence outcome.
3. Documents: upload drawer, completion summary, document delete modal.
4. Admin: create user/department pending state; delete/reset password/rename modal.
5. Audit: loading, empty state và recoverable API error.
6. Desktop và width hẹp: drawer/modal overflow, clipping, focus visibility, Escape close, account menu `aria-expanded`.

## Remaining known UI defects

- Legacy duplicate auth CSS has not been safely removed in Sprint 1; it needs a screenshot-backed cleanup pass.
- Drawer/modal has Escape and focus return but does not implement a full focus-trap library.
- Admin/Audit error state currently shows a message/toast; no explicit Retry button has been added.
- Upload is still synchronous by design and shows no invented percentage progress.
- No public deploy or live endpoint check was performed.

## Push and backup status

- One required attempt `git push -u origin final/v1.0.5` timed out after approximately 64 seconds. No retry was made.
- A Git bundle backup will be created outside tracked source after this QA documentation is committed.
