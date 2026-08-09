# 🏛️ Vietnamese Enterprise Legal & Domain QA System (Advanced RAG)

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109.2-009688)
![Streamlit](https://img.shields.io/badge/Streamlit-1.31.0-FF4B4B)
![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Database-FD0054)
![Ollama](https://img.shields.io/badge/Ollama-LLM-black)

Dự án này xây dựng một hệ thống **Hỏi - Đáp (Question-Answering) nội bộ doanh nghiệp** và **Tư vấn Pháp luật Việt Nam** dựa trên kiến trúc **Advanced RAG (Retrieval-Augmented Generation)**. Hệ thống đóng vai trò như một AI Agent độc lập, có khả năng tra cứu tài liệu nội bộ, kết hợp với các văn bản pháp luật để đưa ra câu trả lời chính xác, tránh hoàn toàn hiện tượng "ảo giác" (Hallucination).

---

## 🌟 Kiến trúc Hệ thống (System Architecture)

Hệ thống được thiết kế theo chuẩn Enterprise RAG Pipeline với 4 module cốt lõi:

1. **Query Processing & Expansion:** 
   - Tự động nhận diện và mở rộng các từ viết tắt phổ biến trong doanh nghiệp và hành chính (ví dụ: `BHXH` -> `Bảo hiểm xã hội`, `HĐLĐ` -> `Hợp đồng lao động`).
2. **Hybrid Retrieval (Truy xuất lai):** 
   - Sử dụng cơ sở dữ liệu vector **Qdrant** kết hợp cả tìm kiếm theo từ khóa (BM25) và tìm kiếm ngữ nghĩa (Semantic Search) để vét cạn tài liệu liên quan.
3. **Cross-Encoder Reranking (Chấm điểm tài liệu):** 
   - Ứng dụng mô hình `BAAI/bge-reranker-v2-m3` để đọc lại văn bản thô, chấm điểm và đẩy các đoạn văn bản (chunks) chứa thông tin chính xác nhất lên top đầu (Top-K).
4. **Context-Aware Generation (Sinh văn bản):** 
   - Sử dụng LLM **Qwen2.5-7B-Instruct** đã được tinh chỉnh (Fine-tuning) bằng **Unsloth** (định dạng ChatML) trên tập dữ liệu pháp lý và nội bộ, giúp mô hình biết cách "đọc" ngữ cảnh và từ chối trả lời nếu không có dữ liệu thật.

---

## 📂 Cấu trúc Dự án (Project Structure)

```text
├── src/
│   ├── agents/
│   │   └── research_agent.py      # AI Agent xử lý luồng (Expand -> Search -> Rerank -> LLM)
│   ├── api/
│   │   ├── main.py                # Backend FastAPI server
│   │   └── routes/
│   │       └── chat.py            # API Endpoint cho Chatbot
│   ├── knowledge/
│   │   └── retriever.py           # Module kết nối Qdrant Hybrid Search
│   └── models/
│       └── llm_factory.py         # Module giao tiếp với Ollama (Local LLM)
├── frontend/
│   └── app.py                     # Giao diện người dùng bằng Streamlit
├── data/
│   ├── ingest.py                  # Script làm sạch và nạp dữ liệu vào Qdrant
│   └── prepare_data.py            # Script chuẩn bị dataset RAG (ChatML) để mang lên Colab
├── notebooks/
│   └── finetune_qwen_unsloth.ipynb # Notebook huấn luyện tinh chỉnh mô hình bằng Unsloth
├── Modelfile                      # Cấu hình System Prompt và Parameter cho Ollama
├── requirements.txt               # Danh sách thư viện phụ thuộc
└── README.md                      # Tài liệu mô tả dự án
🚀 Hướng dẫn Cài đặt & Chạy dự án (Installation & Setup)
1. Yêu cầu hệ thống (Prerequisites)
Python 3.10+

Database: Cài đặt và khởi chạy Qdrant

LLM Engine: Cài đặt Ollama

2. Cài đặt thư viện

Clone repository và cài đặt các thư viện cần thiết:
git clone [https://github.com/Phantom-1023/Hybrid-Chunking-for-Vietnamese-Enterprise-RAG.git](https://github.com/Phantom-1023/Hybrid-Chunking-for-Vietnamese-Enterprise-RAG.git)
cd Hybrid-Chunking-for-Vietnamese-Enterprise-RAG
pip install -r requirements.txt

3. Nạp dữ liệu và Cấu hình Mô hình
Đảm bảo bạn đã tải file mô hình đã fine-tune (.gguf) vào thư mục gốc. Sau đó nạp vào Ollama:
ollama create business-qwen -f Modelfile

4: Chạy Backend (FastAPI):
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
streamlit run frontend/app.py

📊 Đánh giá Mô hình (Model Evaluation Dashboard)
Để đảm bảo hệ thống đạt chuẩn môi trường doanh nghiệp, chất lượng của AI Agent được theo dõi và đánh giá thông qua một Evaluation Dashboard (tích hợp trong Streamlit hoặc công cụ theo dõi riêng), tập trung vào các chỉ số RAG cốt lõi:

Context Precision (Độ chính xác của ngữ cảnh): Đánh giá xem Reranker có đưa các tài liệu liên quan nhất lên Top 1 - Top 3 hay không.

Context Recall (Độ bao phủ của ngữ cảnh): Đánh giá khả năng của Hybrid Search trong việc không bỏ sót tài liệu quan trọng.

Faithfulness (Tính trung thực): Đo lường tỷ lệ các câu trả lời của Qwen2.5 hoàn toàn dựa trên tài liệu (Ngăn chặn Hallucination).

Answer Relevance (Độ liên quan của câu trả lời): Đánh giá xem câu trả lời có đi thẳng

📚 Dữ liệu (Dataset)
Quá trình Fine-tuning mô hình sử dụng tập dữ liệu được kết hợp từ:

Dữ liệu pháp lý Việt Nam dạng RAG-Aware (NamSyntax/Vietnamese-Legal-QA-RAG trên Hugging Face).

Dữ liệu văn bản, quy định nghiệp vụ nội bộ (đã được làm sạch, loại bỏ ký tự rác từ bộ tách từ cũ).

🤝 Lời cảm ơn (Acknowledgments)
Cảm ơn mã nguồn cấu trúc tham khảo từ ngothanhnam0910/Vietnamese-Law-Question-Answering-system.

Sử dụng mô hình từ Qwen và thư viện huấn luyện siêu tốc Unsloth.

Sử dụng Reranker từ BAAI (BGE-M3).
