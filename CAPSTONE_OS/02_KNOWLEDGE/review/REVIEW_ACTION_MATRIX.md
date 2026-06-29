# Ma trận hành động theo Review

| Yêu cầu | Nguồn review | Trạng thái hiện tại | Bằng chứng | Hành động cần làm | Ưu tiên |
|---|---|---|---|---|---|
| Dataset không phụ thuộc doanh nghiệp | Review 1 | Hoàn thành | `sailor2/Vietnamese_RAG`, `K004_REAL_DATASET_DEMO.md`, Streamlit demo dữ liệu thật | Giải thích rõ trong report vì sao dataset public là lựa chọn hợp lệ | Cao |
| Có prototype website/demo | Review 1 | Hoàn thành | Streamlit demo tại `ui/app.py`, lệnh `python -m streamlit run ui/app.py --server.port 8503` | Chuẩn bị kịch bản demo ngắn cho GV | Cao |
| RAG pipeline rõ ràng | Review 1, Review 2 | Hoàn thành | `ARCHITECTURE.md`, CLI verify/index/query | Vẽ lại sơ đồ pipeline trong slide/report | Cao |
| So sánh các chiến lược chunking | Review 1, Review 3 | Một phần | 4 strategy đã verify/index/query; chưa có RAGAS | Chạy evaluation-lite/RAGAS và tạo bảng so sánh | Rất cao |
| RAGAS benchmark định lượng | Mission, Plan, Review 3 | Thiếu | Chưa có `benchmark_results.csv` | Implement/chạy benchmark có giới hạn, không fake kết quả | Rất cao |
| Report khoa học hoàn chỉnh | Review 1, Review 3 | Một phần | Có knowledge artifacts, chưa xác nhận report hoàn chỉnh | Viết chương kết quả sau khi có benchmark thật | Rất cao |
| Slide bảo vệ | Plan, Review 3 | Một phần | Có nội dung nền, chưa xác nhận slide cuối | Tạo 12-15 slide, có demo flow và benchmark chart | Cao |
| Giải thích thay đổi sau Review 1/2 | Review 2, Review 3 | Một phần | Context recovery, decisions, learning docs | Thêm timeline C-003 đến C-008 vào report/slide | Trung bình |
| Xử lý tiếng Việt pha tiếng Anh | Review 1 | Thiếu | Chưa implement; ngoài MVP hiện tại | Đưa vào giới hạn/hướng phát triển, không làm vội trước benchmark | Trung bình |
| Hybrid search/reranking | Review 1 | Thiếu | Mission ghi rõ non-goal MVP | Giải thích là hướng mở rộng sau MVP, không claim đã làm | Trung bình |
| Tinh chỉnh model/tăng độ chính xác | Review 3 | Một phần | Có so sánh strategy hướng tới tối ưu chunking | Sau benchmark, đề xuất cải thiện dựa trên số liệu | Trung bình |
| Không fake benchmark | Mission, Review 3 | Hoàn thành | Quy tắc trong context/decisions | Chỉ đưa kết quả thật vào report/slide | Rất cao |
| Chứng minh source chunks bảo vệ câu trả lời | Nhu cầu demo/defense | Hoàn thành | CLI query và Streamlit hiển thị source chunks | Khi demo, mở source chunks cạnh answer | Cao |
| Quản trị dự án/lập kế hoạch | Review 2, Review 3 | Hoàn thành | `PLAN.md`, `TASK_BOARD.md`, `CURRENT_STATE.md` | Tóm tắt milestone và trạng thái trong slide | Trung bình |
