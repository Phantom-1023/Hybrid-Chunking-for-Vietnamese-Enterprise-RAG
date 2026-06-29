# RUNBOOK

## Cách start demo

Chạy:

```bat
scripts\run_streamlit_safe.bat
```

Mở:

```text
http://localhost:8503
```

## Cách stop demo

Chạy:

```bat
scripts\kill_streamlit.bat
```

Nếu máy quá lag và cần dọn khẩn cấp:

```bat
scripts\kill_python_processes.bat
```

## Cách recover sau khi Codex crash

Codex phải đọc file này trước:

```text
CAPSTONE_OS/00_CONTEXT/CODEX_BOOT.md
```

Sau đó đọc `CURRENT_STATE.md`, `TASK_BOARD.md`, `DECISIONS.md`.

## Lệnh an toàn

```bat
scripts\run_query_smoke_test.bat
scripts\run_verify.bat
python -m py_compile ui\app.py
```

## Lệnh nặng cần PM approval

- Full index lại toàn bộ dataset.
- RAGAS evaluation.
- Evaluation-lite nhiều câu hỏi.
- Bất kỳ lệnh nào gọi API hàng loạt.

## Ghi chú

- Demo hiện không upload file tùy ý.
- Benchmark chưa có thì UI phải hiển thị đúng là chưa chạy.
- Không in API key vào log hoặc câu trả lời.
