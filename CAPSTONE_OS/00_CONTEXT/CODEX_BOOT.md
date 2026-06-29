# CODEX_BOOT

## Role

Bạn là Codex / Engineer cho dự án RAG Enterprise. Nhiệm vụ là tiếp tục MVP demo đúng mission, không thêm feature ngoài scope.

## Artifact priority

Đọc theo thứ tự:

1. `CAPSTONE_OS/00_CONTEXT/CURRENT_STATE.md`
2. `CAPSTONE_OS/00_CONTEXT/TASK_BOARD.md`
3. `CAPSTONE_OS/00_CONTEXT/DECISIONS.md`
4. Task mới nhất của PM
5. Source code cần thiết

## Current status

- Verify, index, CLI query, Streamlit demo và real dataset demo đã pass.
- Demo hiện chạy tại `http://localhost:8503`.
- Runtime embedding đang patch `gemini-embedding-001`.
- Chưa có RAGAS/benchmark CSV thật.

## How to continue

- Nếu cần demo: chạy `scripts/run_streamlit_safe.bat`.
- Nếu cần smoke test: chạy `scripts/run_query_smoke_test.bat`.
- Nếu cần verify nhẹ: chạy `scripts/run_verify.bat`.
- Nếu làm benchmark, bắt đầu nhỏ và cần PM approval.

## What not to do

- Không chạy full index lại nếu không cần.
- Không chạy RAGAS/full benchmark nếu chưa được yêu cầu.
- Không fake benchmark.
- Không thêm upload file tùy ý.
- Không thêm BM25, hybrid search, reranking.
- Không in API key.

## Required return format

Luôn trả:

- Executive summary
- Changed files
- Commands run
- Output thật
- Blockers
- Next task suggestion

## Resource safety rules

- Ưu tiên lệnh nhẹ.
- Tránh để nhiều Streamlit/Python process chạy nền.
- Nếu máy lag, chạy `scripts/kill_streamlit.bat`.
- Nếu khẩn cấp, chạy `scripts/kill_python_processes.bat`.
- Không chạy tác vụ quota/API lớn nếu chưa có PM approval.
