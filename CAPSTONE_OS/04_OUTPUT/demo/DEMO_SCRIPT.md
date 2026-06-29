# Kịch bản demo 5-7 phút

Mục tiêu demo: chứng minh MVP chạy được với dataset public thật, cho phép chọn chunking strategy, hỏi câu hỏi, nhận answer và xem source chunks.

## Chuẩn bị trước demo

- Không chạy lại full index nếu không cần.
- Không chạy RAGAS benchmark trong lúc demo.
- Đảm bảo không có nhiều tiến trình Streamlit/Python nền.
- Nếu máy lag: chạy `scripts/kill_streamlit.bat`.

## Luồng demo chính

### Bước 1: Mở Streamlit

Lệnh:

```powershell
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
```

Nói: "Đây là giao diện demo RAG Enterprise. MVP hiện tập trung vào so sánh chunking strategy trên dataset public tiếng Việt."

Evidence: trình duyệt mở `http://localhost:8503`.

### Bước 2: Giải thích execution patch

UI action: chỉ vào note execution patch trên giao diện.

Nói: "Mission gốc dùng `text-embedding-004`, nhưng API key hiện tại chưa hỗ trợ model đó. Để demo MVP chạy được, hệ thống tạm dùng `gemini-embedding-001`. Quyết định này không thay đổi mission."

Evidence: note trong UI hoặc context file.

### Bước 3: Chọn strategy

UI action: chọn `fixed`, sau đó có thể đổi sang `recursive`.

Nói: "Mỗi strategy tương ứng một ChromaDB collection riêng, giúp so sánh cùng câu hỏi trên các cách chunking khác nhau."

Evidence: sidebar strategy selector.

### Bước 4: Demo với dữ liệu thật

UI action:

1. Mở section/tab "Demo với dữ liệu thật".
2. Random hoặc chọn một record.
3. Chỉ vào `record_id`, original question, ground_truth và context preview.

Nói: "Câu hỏi này lấy từ dataset public, không phải câu hỏi khóa cứng. Ground truth dùng để so sánh thủ công với câu trả lời sinh ra."

Evidence: record thật, ground truth, context preview.

### Bước 5: Hỏi bằng câu hỏi này

UI action: bấm "Hỏi bằng câu hỏi này".

Nói: "Pipeline sẽ embed câu hỏi, truy xuất top-k source chunks từ collection theo strategy đã chọn, rồi dùng LLM sinh answer."

Evidence: answer xuất hiện, kèm top source chunks.

### Bước 6: Giải thích source chunks

UI action: mở/scroll source chunks.

Nói: "Source chunks cho thấy câu trả lời dựa trên đoạn nào. Đây là phần giúp kiểm tra hallucination và bảo vệ câu trả lời khi review."

Evidence: ít nhất 3 source chunks và metadata nếu có.

### Bước 7: Nói rõ phần benchmark đang pending

UI action: mở benchmark section.

Nói: "RAGAS benchmark chưa chạy nên hệ thống không hiển thị số giả. Bước tiếp theo là chạy benchmark thật để có `benchmark_results.csv` và biểu đồ so sánh."

Evidence: message benchmark pending hoặc không có CSV.

## Fallback CLI nếu Streamlit lỗi

Lệnh smoke test:

```powershell
python main.py --mode query --strategy fixed --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

Nếu muốn test strategy khác:

```powershell
python main.py --mode query --strategy recursive --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

Nói: "Nếu UI gặp lỗi môi trường, pipeline lõi vẫn chạy qua CLI: chọn strategy, embed query, query ChromaDB, sinh answer và in source chunks."

Evidence cần thấy trên console:

- Strategy được chọn.
- Question.
- Answer hoặc retrieval-only fallback.
- Ít nhất 3 source chunks.

## Câu nói kết demo

"MVP hiện đã chứng minh luồng RAG end-to-end trên dataset public tiếng Việt. Phần còn thiếu để hoàn thiện báo cáo khoa học là benchmark RAGAS thật, không dùng số liệu giả."
