# Sprint 1 changelog — v1.0.5

Implementation commit: `fb55726b6204fcfd5f09da2a68fbba80bf173e1f`.

## Files changed

- `src/__init__.py`
- `webapp/app.py`
- `webapp/static/index.html`
- `webapp/static/app.js`
- `webapp/static/styles.css`
- `tests/test_webapp_frontend_polish.py`

## Improvements implemented

1. **Release hygiene**: visible static-resource version labels and FastAPI/package version now use `v1.0.5`; a regression test rejects `semi-ver1.0.4` from the frontend page.
2. **Scoped async feedback**: login, setup, registration, profile/password change, chat, document upload, create department and create user now use a shared pending helper. It disables only the submitting control, sets `aria-busy`, changes the Vietnamese label, and restores the control in `finally`.
3. **Recoverable loading/empty states**: Admin/Audit navigation now gives a loading/error state and toast instead of silently failing. Audit displays an explicit empty row.
4. **Chat evidence boundary**: when search returns no usable citations, the UI renders a no-evidence outcome and does not display the returned answer as grounded. When present, the API-returned retrieval method is shown unobtrusively beside the evidence count.
5. **Upload completion**: successful synchronous upload now shows title, extracted chunk count, scope and selected department when available. It does not claim background percentage progress.
6. **Destructive/demo actions**: a small branded modal intercepts delete document/user/department, reset password and rename department. It names the action, has Cancel/Confirm, has a destructive visual treatment, supports Escape and preserves backend API authorization.
7. **Basic accessibility/responsive polish**: account menu has `aria-expanded`; modal is a semantic dialog; Escape closes modal/drawers/menu; focus-visible and narrow-width styles were added.

## Behavior and risk notes

- No API contract, ACL rule, retrieval architecture, benchmark artifact, database migration or dependency was changed.
- The modal only changes browser-side interaction. Delete/reset/rename still use the existing authorized backend endpoints.
- The no-evidence branch deliberately prefers an explicit boundary over presenting a possibly ungrounded answer.
- The retrieval method is displayed only from `result.retrieval.method`; it does not assert Hybrid/Cross-Encoder availability beyond the actual response.

## Deliberately deferred

- Removal/reformatting of remaining legacy duplicate auth CSS was deferred: the stylesheet is accumulated/minified and no visual server run was available to verify a broader removal safely. New CSS is scoped to the active UI components; no visual redesign was introduced.
- BM25 lifecycle/cache redesign, OCR, GraphRAG, agents, vector migration, retraining, RAGAS and public reranker deployment remain out of scope.
- Full keyboard focus trapping and a manual visual responsive pass remain pending.
