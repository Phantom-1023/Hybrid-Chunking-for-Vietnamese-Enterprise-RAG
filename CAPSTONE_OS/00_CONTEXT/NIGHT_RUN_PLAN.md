# NIGHT RUN PLAN

Status: `APPROVED FOR EXECUTION`

Mục tiêu: hoàn thiện bản cơ bản có thể bảo vệ của Vietnamese Enterprise RAG,
không phá MVP hiện tại và không claim vượt quá bằng chứng.

## 1. Definition of Done cơ bản

- Dense + BM25 -> Hybrid RRF -> Cross-Encoder reranker -> top-5 evidence -> LLM/citation.
- Có no-rerank, MMR, base Cross-Encoder và fine-tuned Cross-Encoder trên cùng locked test set.
- Có split/leakage contract, training history, validation checkpoint, checksum,
  before/after metrics và error analysis.
- Web có login, user/phòng ban/role, document ACL và admin tối thiểu.
- ACL được áp dụng trước retrieval/reranking.
- Docker chạy local; có temporary deployment nếu hạ tầng miễn phí cho phép.
- Có README, evidence index, demo script, report/slide skeleton và defense Q&A.

## 2. Pha thực thi

| Pha | Việc chính | Gate bắt buộc | Output |
|---|---|---|---|
| P0 — PASS | Git/worktree safety, environment, source-of-truth | Không mất thay đổi cũ; không chạm `main` | `review2-mvp-demo`, Python 3.11 `.venv`, 6 tests pass, secret scan sạch |
| P1 — PASS | Dataset audit, split, dense/BM25/Hybrid baseline | Leakage checks và targeted tests pass | Locked split + real retrieval metrics |
| P2 — ACTIVE | Smoke train rồi fine-tune reranker | Chọn checkpoint bằng validation | Checkpoint/history/SHA256 |
| P3 | Tích hợp reranker vào query pipeline | Test chứng minh checkpoint được gọi thật | End-to-end top-20 -> top-5 |
| P4 | FigJam/Figma và web shell | Luồng UX/ACL được duyệt bằng testable spec | Login/chat/admin/document UI |
| P5 | Auth, department, role và document ACL | Cross-department denial test pass | Multi-user MVP |
| P6 | Docker, temporary deploy, smoke/load test | Health check + evidence; không overclaim | Local package + URL nếu pass |
| P7 | README/report/slides/demo/defense | Mọi claim trỏ được tới evidence | Defense-ready pack |

P0 evidence:

- HEAD đã gắn vào `review2-mvp-demo`, cùng commit `231ba4f` với remote.
- Hash tracked diff và status trước/sau khi gắn nhánh không đổi.
- `.venv` dùng Python 3.11.9; chỉ cài foundation `pytest` và `python-dotenv`.
- `scripts/run_safe_checks.ps1`: preflight pass, secret scan 0 hit, 4 tests pass.
- `tests/test_dataset_audit.py`: 2 tests pass.
- Active ML/web stack vẫn chưa được cài; chỉ cài theo lát cắt P1 trở đi.

P1 evidence:

- Dataset snapshot: 1.141 rows, 5.705 passages, 4.641 unique passages.
- Label gate: semantic audit 50/50 `context0_positive`, 0 ambiguous, 0 fail.
- Split: Protocol A, seed 42, train/dev/test `913/114/114`.
- Cross-split duplicate question/pair conflicts: 0.
- Locked-test BM25: MRR `0.660`, Hit@5 `0.974`, Recall@20 `1.000`.
- Locked-test Dense E5: MRR `0.750`, Hit@5 `0.947`, Recall@20 `0.991`.
- Locked-test Hybrid RRF: MRR `0.669`, Hit@5 `0.965`, Recall@20 `1.000`.
- Hybrid dùng RRF constant 60 đã định trước; không tune bằng test.
- P2 initial pairs: train 4.564, dev 569, test 570; raw text chỉ nằm
  trong `.cache/reranker/groups`.

## 3. Điều phối model

- `Sol/high`: P0, split/leakage, security/ACL, integration review và lỗi khó.
- `Terra/medium`: implementation, debugging và research synthesis thông thường.
- `Luna/low`: inventory, tài liệu, checklist và kiểm tra cơ học.
- Không chạy nhiều writer trên cùng file. Task chính là integration owner.
- Task phụ bắt đầu read-only; chỉ được ghi khi có file scope riêng được task chính giao.
- Sau một lần thử có verification thất bại mới nâng model một bậc.

### Task conversations đang chạy

| Task | Model | Quyền lượt đầu | Thread |
|---|---|---|---|
| Scientific Core Gatekeeper | Sol/high | Read-only | `019fb2e9-1c17-7143-b28f-e3e7b5fbcab9` |
| Web/Figma/Auth/Deploy Architect | Terra/medium | Read-only | `019fb2e9-322d-74a1-9f16-e7cfa3aee24a` |
| Evidence/Git/Defense Inventory | Luna/low | Read-only | `019fb2e9-4937-7261-9a97-1a4e06903b18` |

Task chính là integration owner và writer mặc định.

## 4. Git contract

- Target duy nhất: `review2-mvp-demo`.
- Không push hoặc merge trực tiếp vào `main`.
- Không stage toàn bộ dirty worktree.
- Mỗi commit chỉ chứa một thay đổi có thể giải thích và đã verification.
- Trước push: review diff, targeted tests và secret scan.
- Không commit `.env`, credential, private data hoặc checkpoint lớn.

## 5. Secret contract

- Credential chỉ nhập vào secret manager hoặc environment variable.
- Không ghi password/token vào Markdown, source code, commit, terminal summary hay log.
- Nếu cần user takeover cho password/2FA thì đó là hard stop ngắn; các pha độc lập vẫn tiếp tục.

## 6. Autonomous loop

`inspect -> implement one slice -> verify -> record evidence -> commit -> checkpoint -> next slice`

Nếu một task bị chặn, ghi rõ blocker và chuyển sang task độc lập. Chỉ dừng toàn bộ
khi có nguy cơ mất dữ liệu, lộ secret, phát sinh chi phí, push sai nhánh hoặc phải
thay Mission Contract.

## 7. Checkpoint report sau mỗi pha

1. Kết quả đạt được.
2. Tests/checks đã chạy và verdict.
3. Files/artifacts thay đổi.
4. Commit/push status.
5. Claim nào đã được phép và claim nào vẫn cấm.
6. Blocker và pha kế tiếp.
