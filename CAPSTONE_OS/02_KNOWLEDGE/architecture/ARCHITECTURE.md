# ARCHITECTURE.md
> RAG Enterprise — GSU26AI09

---

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        STREAMLIT UI                             │
│          Q&A Interface  │  Benchmark Dashboard                  │
└─────────────┬───────────────────────────┬───────────────────────┘
              │ user query                │ load results
              ▼                           ▼
┌─────────────────────┐      ┌────────────────────────┐
│   QUERY PIPELINE    │      │   BENCHMARK RESULTS    │
│                     │      │   (CSV / JSON cached)  │
│  1. Embed query     │      └────────────────────────┘
│     Gemini embed    │
│  2. Retrieve top-k  │◄──── ChromaDB (4 collections)
│     ChromaDB        │
│  3. Generate answer │
│     Gemini Flash    │
└─────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    INDEXING PIPELINE                            │
│  (chạy 1 lần offline, kết quả lưu vào ChromaDB)                │
│                                                                 │
│  HuggingFace Dataset                                            │
│  sailor2/Vietnamese_RAG                                         │
│  (BKAI_RAG, 50 docs)                                            │
│         │                                                       │
│         ▼                                                       │
│  [Preprocessor]  join List[str] → str                          │
│         │                                                       │
│         ├──► [Fixed Chunker]    → collection: fixed            │
│         ├──► [Recursive Chunker]→ collection: recursive        │
│         ├──► [Semantic Chunker] → collection: semantic         │
│         └──► [Paragraph Chunker]→ collection: paragraph        │
│                     │                                           │
│                     ▼                                           │
│           Gemini text-embedding-004                             │
│                     │                                           │
│                     ▼                                           │
│              ChromaDB (local)                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    EVALUATION PIPELINE                          │
│  (chạy 1 lần, export kết quả)                                   │
│                                                                 │
│  RAGAS test set ◄── Vietnamese_RAG Q&A pairs                   │
│         │                                                       │
│         ▼                                                       │
│  For each chunking strategy:                                    │
│    retrieve context → generate answer → RAGAS score            │
│         │                                                       │
│         ▼                                                       │
│  Output: benchmark_results.csv                                  │
│  Metrics: Faithfulness │ Answer Relevancy                       │
│           Context Recall │ Context Precision                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Module Responsibilities

| Module | File(s) | Trách nhiệm | Ai làm |
|--------|---------|-------------|--------|
| **Preprocessor** | `data_loader.py` | Load `sailor2/Vietnamese_RAG`, join `context: List[str]` → `str`, làm sạch unicode | Backend/Data Engineer |
| **Chunkers** | `chunkers.py` | Implement 4 chiến lược: Fixed, Recursive, Semantic, Paragraph. Output chuẩn hóa: `List[str]` | AI Engineer |
| **Indexer** | `indexer.py` | Nhận chunks → gọi Gemini embedding → upsert vào ChromaDB với collection name tương ứng | Backend/Data Engineer |
| **Retriever** | `retriever.py` | Nhận query → embed → query ChromaDB → trả `top_k` chunks | AI Engineer |
| **Generator** | `generator.py` | Nhận query + context chunks → gọi Gemini Flash → trả answer string | AI Engineer |
| **Evaluator** | `evaluator.py` | Chạy RAGAS pipeline cho từng strategy, export `benchmark_results.csv` | AI Engineer |
| **Streamlit App** | `app.py` | Tab 1: Q&A live; Tab 2: Benchmark dashboard (bảng + biểu đồ) | Fullstack/UI Engineer |
| **Config** | `config.py` | API keys, chunk sizes, top_k, collection names, dataset config | DevOps (Uẩn) |
| **Pipeline Runner** | `main.py` | CLI entry point: `--mode index | evaluate | demo` | DevOps (Uẩn) |

---

## Data Flow

### Flow 1 — Indexing (offline)
```
Dataset (HuggingFace)
  → Preprocessor (join passages, clean)
  → Chunker[strategy] (split thành chunks)
  → Gemini text-embedding-004 (embed mỗi chunk)
  → ChromaDB.collection[strategy].add()
```

### Flow 2 — Q&A Query (online / Streamlit)
```
User query (string)
  → Gemini text-embedding-004 (embed query)
  → ChromaDB.collection[selected_strategy].query(top_k=5)
  → Gemini Flash (generate: system_prompt + context + question)
  → Display answer + source chunks
```

### Flow 3 — RAGAS Evaluation (offline / one-shot)
```
For each strategy in [fixed, recursive, semantic, paragraph]:
  For each (question, ground_truth) in test_set:
    → Flow 2 → get (answer, contexts)
    → RAGAS.evaluate(question, answer, contexts, ground_truth)
  → Aggregate scores
→ Export benchmark_results.csv
→ Display trong Streamlit Tab 2
```

### Sơ đồ dữ liệu đơn giản
```
sailor2/Vietnamese_RAG
  ├── question        → RAGAS input
  ├── ground_truth    → RAGAS input
  └── context[list]   → join → chunk → embed → store
```

---

## Why This Architecture

| Quyết định | Lý do |
|------------|-------|
| **Gemini Flash + text-embedding-004** | API-first constraint; chi phí < $15/tháng; không cần GPU; ổn định cho demo |
| **ChromaDB (local)** | Zero setup, không cần server, persist to disk, đủ cho 50 docs × 4 strategies |
| **4 collection riêng biệt** | Isolate hoàn toàn kết quả giữa các chiến lược; không cross-contaminate khi benchmark |
| **RAGAS** | Chuẩn đánh giá RAG được học thuật công nhận; có sẵn Python package; phù hợp báo cáo khoa học |
| **Streamlit** | 1 file = 1 demo; không cần deploy; GV demo trực tiếp trên laptop |
| **sailor2/Vietnamese_RAG** | Public dataset; không phụ thuộc doanh nghiệp; giải quyết feedback Review 1 về dataset |
| **API calls batch nhỏ** | Tránh rate limit Gemini trong lúc demo; có thể cache kết quả embedding |

### Keep it achievable within 5 hours

Toàn bộ hệ thống chia thành 3 pipeline độc lập:
- **Indexing**: chạy offline 1 lần, ~20 phút, kết quả persist
- **Evaluation**: chạy offline 1 lần, export CSV, không cần chạy lại khi demo
- **Demo**: Streamlit chỉ load từ ChromaDB + CSV đã có → không bị rate limit khi demo live

→ **Demo day = đọc từ disk, không gọi nhiều API**
