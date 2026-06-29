# PLAN.md
> RAG Enterprise — GSU26AI09  
> Mục tiêu: Sẵn sàng bảo vệ lần 1 — tối ưu cho chấm điểm

---

## Tổng quan thời gian

```
Tổng: 5 giờ (300 phút)
├── M1: Environment & Data Check       30 phút
├── M2: ChromaDB Indexing (4 strategy) 60 phút
├── M3: RAGAS Evaluation               60 phút
├── M4: Streamlit Demo Polish          45 phút
├── M5: Report & Slides                75 phút
└── Buffer (fix bugs, rate limit)      30 phút
```

---

## Milestone 1 — Environment & Data Verification

**Objective:** Đảm bảo toàn bộ team chạy được cùng môi trường, dataset load đúng, 4 chunker hoạt động.

**Deliverable:**
- `requirements.txt` cập nhật (thêm chromadb, ragas, streamlit nếu thiếu)
- Script `python main.py --mode verify` in ra: dataset shape, sample chunks của 4 strategies

**Estimated effort:** 30 phút

**Priority:** 🔴 Critical — không làm M2–M5 được nếu thiếu

**Dependencies:** Không có (starting point)

**Checklist:**
- [ ] `sailor2/Vietnamese_RAG` load được (BKAI_RAG config, 50 docs)
- [ ] `context: List[str]` được join đúng thành `str`
- [ ] Fixed chunker → output ≥ 1 chunk
- [ ] Recursive chunker → output ≥ 1 chunk
- [ ] Semantic chunker → output ≥ 1 chunk (dùng `keepitreal/vietnamese-sbert`)
- [ ] Paragraph chunker → output ≥ 1 chunk
- [ ] Gemini API key hợp lệ (test 1 embedding call)

---

## Milestone 2 — ChromaDB Indexing (4 Collections)

**Objective:** Ingest toàn bộ 50 documents với 4 chiến lược chunking vào 4 ChromaDB collections riêng biệt.

**Deliverable:**
- `python main.py --mode index` chạy xong không lỗi
- 4 collections trong ChromaDB: `collection_fixed`, `collection_recursive`, `collection_semantic`, `collection_paragraph`
- Mỗi collection có thể query được (test: 1 query trả về top-5 chunks)

**Estimated effort:** 60 phút

**Priority:** 🔴 Critical — M3 và M4 phụ thuộc hoàn toàn vào M2

**Dependencies:** M1 xong

**Checklist:**
- [ ] `indexer.py` batch embed + upsert vào ChromaDB
- [ ] Xử lý Gemini rate limit: `time.sleep(1)` giữa các batch
- [ ] Verify: `collection.count()` > 0 cho cả 4 collections
- [ ] Persist ChromaDB to disk (không mất khi restart)
- [ ] Log: số chunks mỗi strategy (Fixed: N, Recursive: N, Semantic: N, Paragraph: N)

**Ghi chú kỹ thuật:**
- Batch size khuyến nghị: 10 docs/batch để tránh rate limit
- ChromaDB path: `./chroma_db/` (relative, không absolute)
- Collection naming: lowercase, không dấu cách

---

## Milestone 3 — RAGAS Evaluation

**Objective:** Chạy RAGAS benchmark cho cả 4 chiến lược và export kết quả có thể trình bày được.

**Deliverable:**
- `benchmark_results.csv` với cột: `strategy | faithfulness | answer_relevancy | context_recall | context_precision | avg_score`
- Kết quả rõ ràng thể hiện sự khác biệt giữa các chiến lược

**Estimated effort:** 60 phút

**Priority:** 🔴 Critical — đây là **research contribution** chính, GV chắc chắn hỏi

**Dependencies:** M2 xong

**Checklist:**
- [ ] `evaluator.py` chạy RAGAS cho từng strategy
- [ ] Dùng `question` + `ground_truth` từ `sailor2/Vietnamese_RAG` làm test set
- [ ] Số lượng test questions: tối thiểu 20, lý tưởng 50
- [ ] Export kết quả ra `benchmark_results.csv`
- [ ] Kiểm tra: không có `NaN` trong kết quả RAGAS
- [ ] Ghi lại thời gian chạy mỗi strategy (thông tin thêm cho báo cáo)

**Xử lý rủi ro rate limit:**
- Nếu bị throttle: chạy từng strategy riêng, cache kết quả trung gian
- Fallback: chạy với 20 questions thay vì 50 (đủ để so sánh)

---

## Milestone 4 — Streamlit Demo Polish

**Objective:** Demo chạy ổn định, không crash, đủ ấn tượng khi GV xem live.

**Deliverable:**
- `streamlit run app.py` hoạt động
- Tab 1 (Q&A): nhập câu hỏi → hiện câu trả lời + source chunks đã dùng + có thể chọn strategy
- Tab 2 (Benchmark): bảng kết quả RAGAS + 1 biểu đồ bar chart so sánh avg_score

**Estimated effort:** 45 phút

**Priority:** 🟠 High — GV sẽ yêu cầu demo live trong buổi bảo vệ

**Dependencies:** M2 (ChromaDB sẵn), M3 (CSV results sẵn)

**Checklist:**
- [ ] Tab Q&A: dropdown chọn strategy, input box, button Submit
- [ ] Hiển thị answer rõ ràng, có section "Nguồn tham khảo" show top-3 chunks
- [ ] Tab Benchmark: load từ `benchmark_results.csv` (không gọi API khi demo)
- [ ] Bar chart: matplotlib hoặc Altair — 4 bars, mỗi bar = 1 strategy, height = avg_score
- [ ] Test trước với 3 câu hỏi mẫu, đảm bảo không crash
- [ ] Đặt sẵn câu hỏi demo trong sidebar (pre-filled examples) để GV test nhanh

**Ghi chú demo-day:**
- ChromaDB + benchmark CSV đã load sẵn → không gọi API nhiều
- Chỉ Q&A live mới gọi Gemini Flash → tối đa 5 calls trong buổi bảo vệ

---

## Milestone 5 — Report & Defense Slides

**Objective:** Hoàn thiện báo cáo khoa học và slide bảo vệ, tích hợp kết quả RAGAS thực nghiệm.

**Deliverable:**
- Báo cáo: chèn bảng `benchmark_results` vào chương Kết quả + phân tích ≥ 1 trang
- Slides: 12–15 slide, có slide riêng cho bảng/biểu đồ so sánh 4 chiến lược
- Mục "Hướng phát triển" đề cập xử lý mixed Việt-Anh và Hybrid Retrieval (respond to Review 1)

**Estimated effort:** 75 phút

**Priority:** 🟠 High — GV đã nói "Hoàn thiện report" là yêu cầu BV lần 1

**Dependencies:** M3 xong (cần số liệu thực)

**Checklist:**
- [ ] Chương Kết quả: bảng RAGAS đủ 4 chiến lược × 4 metrics
- [ ] Phân tích: chiến lược nào tốt nhất, lý do tại sao (theo lý thuyết chunking)
- [ ] Chương Thảo luận: hạn chế (dataset size, rate limit), hướng mở rộng
- [ ] Hướng mở rộng: đề cập xử lý tiếng Việt–Anh hybrid (đáp ứng comment Review 1)
- [ ] Slides: slide 1 (title) → slide 2 (vấn đề + research question) → ... → slide N (Q&A)
- [ ] Kiểm tra: tên thành viên, MSSV, tên GVHD đúng trên cover

---

## Dependency Map

```
M1 (Verify)
  └──► M2 (Index)
         ├──► M3 (Evaluate) ──► M5 (Report)
         └──► M4 (Demo)     ──► M5 (Slides)
```

---

## Phân công khuyến nghị

| Milestone | Lead | Support |
|-----------|------|---------|
| M1 | Uẩn (DevOps) | Tất cả verify local |
| M2 | Backend/Data Engineer | Uẩn review config |
| M3 | AI Engineer | Backend/Data hỗ trợ data prep |
| M4 | Fullstack/UI Engineer | AI Engineer test cases |
| M5 | Cả team | Uẩn coordinate, AI Engineer viết phân tích |

---

## Red Lines (không được phép trượt deadline)

| Hạng mục | Tại sao critical |
|----------|-----------------|
| M2 phải xong trước khi ngủ ngày 1 | M3 cần nhiều thời gian + rate limit risk |
| M3 phải có kết quả số trước M5 | Không có số = không có báo cáo khoa học |
| Demo không gọi API trong lúc present | Rate limit = demo crash = mất điểm |
| Không thêm feature mới sau M2 | Scope creep là risk lớn nhất với 5 giờ còn lại |
