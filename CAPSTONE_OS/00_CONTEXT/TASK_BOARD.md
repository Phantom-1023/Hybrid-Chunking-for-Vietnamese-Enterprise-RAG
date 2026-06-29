# TASK_BOARD

## Done tasks

- C-003: Verify mode.
- C-004: Indexing pipeline cho ChromaDB.
- C-005: Execution patch embedding và index MVP.
- C-006: CLI retrieval/query.
- C-007: Streamlit demo tối thiểu.
- C-008: Demo bằng dữ liệu thật từ public dataset.

## Current task

- C-009: Tạo context recovery và resource guard.

## Next recommended tasks

- C-010: Tạo evaluation-lite có giới hạn nhỏ để sinh `benchmark_results.csv` thật.
- C-011: Hiển thị benchmark thật trong Streamlit.
- C-012: Chuẩn bị nội dung báo cáo/slide từ số liệu thật.

## Stage gate rule

- Không chuyển task nếu chưa có output thật.
- Không fake benchmark.
- Không chạy tác vụ nặng nếu chưa có PM approval.
- Không đổi mission documents im lặng.

## Evidence để pass một task

- Có lệnh đã chạy.
- Có output thật từ console hoặc UI.
- Có danh sách file thay đổi.
- Có blocker/risk rõ ràng nếu chưa hoàn tất.
- Với demo UI: phải có URL hoặc HTTP check.
- Với benchmark: phải có file CSV thật và số liệu sinh từ pipeline thật.
