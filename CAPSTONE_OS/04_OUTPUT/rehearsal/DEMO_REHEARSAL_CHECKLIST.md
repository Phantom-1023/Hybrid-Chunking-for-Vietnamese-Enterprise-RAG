# Checklist rehearsal demo

## Trước khi demo

- Đóng tab/app không cần thiết để tránh lag.
- Không chạy lại full index.
- Không chạy full RAGAS.
- Không in hoặc mở API key.
- Kiểm tra có file `benchmark_results.csv`.
- Kiểm tra thư mục `chroma_db/` còn tồn tại.
- Mở sẵn slide, terminal và trình duyệt.

## Lệnh cần chạy

Ưu tiên dùng lệnh an toàn:

```powershell
python -m streamlit run ui/app.py --server.port 8503 --server.address localhost
```

Nếu đã có server chạy sẵn, chỉ mở trình duyệt:

```text
http://localhost:8503
```

Nếu cần smoke test CLI:

```powershell
python main.py --mode query --strategy fixed --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

## Trình tự click trong UI

1. Mở `http://localhost:8503`.
2. Chỉ vào note: demo dùng `gemini-embedding-001`.
3. Sidebar: chọn strategy, nên chọn `paragraph` nếu muốn demo theo kết quả evaluation-lite tốt nhất.
4. Mở tab "Demo với dữ liệu thật".
5. Bấm random record hoặc chọn một record.
6. Chỉ vào `record_id`, original question, ground truth và context preview.
7. Bấm "Hỏi bằng câu hỏi này".
8. Chờ answer hiện ra.
9. Mở 2-3 source chunks đầu tiên.
10. Mở tab "Benchmark evaluation-lite".
11. Chỉ bảng benchmark, biểu đồ `avg_score` và best strategy.
12. Nói rõ: evaluation-lite chưa phải full RAGAS.

## Cần nói khi demo

- "Câu hỏi này lấy từ dataset public, không phải câu hỏi khóa cứng."
- "Mỗi strategy tương ứng một ChromaDB collection riêng."
- "Source chunks là bằng chứng cho câu trả lời."
- "Benchmark hiện tại là evaluation-lite trên 5 mẫu, chưa phải full RAGAS."
- "Trong evaluation-lite hiện tại, paragraph có `avg_score = 0.8354`, nhưng đây chưa phải kết luận học thuật cuối cùng."

## Nếu Streamlit fails

1. Không hoảng, chuyển sang CLI fallback.
2. Nói: "Nếu UI gặp lỗi môi trường, pipeline lõi vẫn chạy qua CLI."
3. Chạy:

```powershell
python main.py --mode query --strategy fixed --question "Minh Tú đã đạt thành tích gì trong Asia Next Top Model mùa 5?"
```

4. Chỉ console output: selected strategy, question, answer, source chunks.
5. Nếu port bị chiếm, mở đúng URL đang chạy hoặc đổi port:

```powershell
python -m streamlit run ui/app.py --server.port 8504 --server.address localhost
```

## Nếu Gemini/API fails

- Nói: "Phần retrieval vẫn chứng minh được source chunks; LLM có thể phụ thuộc API/quota."
- Dùng source chunks để giải thích pipeline retrieval.
- Không nói hệ thống bị sai; nói đây là rủi ro runtime API.
- Nếu query CLI vẫn trả source chunks, dùng đó làm bằng chứng.

## Nếu benchmark tab không load

- Kiểm tra `benchmark_results.csv` có ở root project không.
- Nếu tab không hiển thị, mở trực tiếp CSV hoặc đọc số trong slide:
  - fixed: `avg_score = 0.3344`
  - recursive: `avg_score = 0.3410`
  - semantic: `avg_score = 0.3313`
  - paragraph: `avg_score = 0.8354`
- Nói: "Đây là file CSV thật từ evaluation-lite; UI chỉ là lớp hiển thị."

## Câu chốt demo

"Demo chứng minh MVP RAG chạy end-to-end trên dataset public tiếng Việt, có source chunks để kiểm chứng và có benchmark-lite thật. Full RAGAS và enterprise production là bước tiếp theo."
