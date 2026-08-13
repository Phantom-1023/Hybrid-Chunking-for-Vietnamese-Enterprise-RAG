# Sprint 2 structural UI QA — v1.0.5

## Revisions

- Starting SHA: `3e5b5e055a3e04886fa6ad99e2df418feedd3bd7`
- Structural UI implementation SHA: `65e5aecfd98bb8ed86a5b1181d5b8f2b77465e43`
- Base line: `58df599 -> 69dc58d -> fb55726 -> 3e5b5e0 -> 65e5aec`

## Files changed

- `webapp/grounded_llm.py`
- `webapp/static/app.js`
- `webapp/static/styles.css`
- `tests/test_webapp_frontend_polish.py`
- `tests/test_grounded_llm_copy.py`

## Exact fixes

1. **Source drawer navigation**: drawer source now renders an explicit `Đóng` control, receives focus when opened, closes without reload, restores focus to the invoking citation/document button, and Escape closes it through `closeDrawer("source-drawer")`.
2. **Long source title**: source drawer header now has a constrained title container with `overflow-wrap:anywhere` and `word-break:break-word`; close control is flex-fixed so it remains reachable on narrow layouts.
3. **Evidence-only wording**: unconfigured `GroundedLLM` now explicitly labels evidence-retrieval mode and describes bounded accessible sources. It does not claim a chatbot/LLM is configured. The configured generation path is unchanged.
4. **Content visibility**: desktop conversation has bottom padding above sticky composer; at narrow width composer becomes non-sticky and the source drawer header stays usable while the drawer scrolls.
5. **No native dialogs**: obsolete bubble handlers containing `window.confirm()`/`window.prompt()` were removed. Main demo delete/reset/rename remains routed through the Sprint 1 branded modal and existing backend endpoints.
6. **Control consistency**: no code change was required. Existing `+ Mời người dùng` and `+ Thêm phòng ban` controls already use `secondary compact`; changing their styling without screenshot verification would add risk.

## Guardrails confirmed

- No changes to `webapp/ingestion.py`, retrieval modules, chunk size/overlap, benchmark data, ACL/RLS, database/migration, dependency, deployment or training files.
- Source checks after patch: no `window.confirm(`, no `window.prompt(` and no stale `Chưa cấu hình chatbot` text in `webapp/`.

## Test results

| Scope | Exact command | Result |
|---|---|---|
| JavaScript syntax | `node --check webapp\static\app.js` | Exit `0`. |
| Focused frontend/ACL | `C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider tests\test_webapp_frontend_privacy.py tests\test_webapp_frontend_polish.py tests\test_grounded_llm_copy.py tests\test_webapp_product_hardening.py tests\test_webapp_acl.py --basetemp .\P0_RELEASE\pytest-sprint2-focused` | `17 passed, 2 warnings in 7.70s`. |
| Full suite | `C:\Users\hieuu\Documents\Đồ Án\.p0-venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .\P0_RELEASE\pytest-sprint2-full` | `86 passed, 2 warnings in 17.15s`; wall-clock `18.54s`; exit `0`. |

Warnings remain Pydantic class-based config deprecation and Starlette multipart pending-deprecation. Zero test failure.

## Visual QA status

**NOT PASSED / NOT CLAIMED.** Local server/browser visual execution was previously blocked by the execution-permission layer before a server process was created. This sprint did not use a workaround.

Manual visual checks still required when a safe local run is available:

1. Open a citation then source drawer; confirm explicit `Đóng`, Escape and focus return.
2. Use a long filename on desktop and narrow width; confirm title wraps and close control remains visible.
3. Run a search with evidence-only mode; confirm professional wording and citations remain visible.
4. Scroll a long chat result and source drawer; confirm last evidence remains reachable above/below composer.
5. Check Documents/Admin controls at desktop/narrow widths; ensure compact create buttons and no horizontal overflow.

## Remaining cosmetic issues

- Accumulated legacy auth CSS has not been reformatted or broadly removed; it requires screenshot-backed cleanup, not this micro patch.
- No full focus trap was introduced for drawers/modals.
- No screenshot artifacts were created and no public deployment was performed.
