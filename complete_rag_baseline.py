import os
import re
import json
import time
import urllib.request
import urllib.error
import numpy as np
from typing import List, Dict, Any

# Tự động kiểm tra và cài đặt các thư viện cần thiết phục vụ bài toán
try:
    from datasets import load_dataset
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "datasets", "-q"])
    from datasets import load_dataset

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "sentence-transformers", "-q"])
    from sentence_transformers import SentenceTransformer

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    import subprocess
    subprocess.run(["pip", "install", "rank_bm25", "-q"])
    from rank_bm25 import BM25Okapi

# Cấu hình tham số lõi của hệ thống RAG
CONFIG = {
    "embedding_model": "BAAI/bge-m3", 
    "gemini_model": "gemini-2.5-flash",
    "api_key": os.environ.get("GEMINI_API_KEY", ""), 
    "chunk_size_words": 150, 
    "chunk_overlap_words": 30, 
    "top_k": 3 
}

class VietnameseWordSplitter:
    """Bộ phân mảnh văn bản dựa trên đơn vị Từ nhằm bảo toàn ngữ nghĩa Tiếng Việt"""
    def __init__(self, chunk_size: int = 150, overlap: int = 30):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        
        # Chuẩn hóa khoảng trắng văn bản thô
        clean_text = re.sub(r'\s+', ' ', text.strip())
        words = clean_text.split(' ')
        
        chunks = []
        step = self.chunk_size - self.overlap
        if step <= 0:
            step = self.chunk_size

        for i in range(0, len(words), step):
            chunk_words = words[i:i + self.chunk_size]
            # Loại bỏ các đoạn quá ngắn không đủ cấu thành ngữ cảnh
            if len(chunk_words) > 5:
                chunks.append(" ".join(chunk_words))
                
        return chunks

class ProductionHybridRetriever:
    """Hệ thống tìm kiếm lai kết hợp Vector không gian và Tần suất từ khóa BM25"""
    def __init__(self, chunks: List[str], model_name: str):
        if not chunks:
            raise ValueError("Danh sách dữ liệu nạp vào bộ lưu trữ không được để trống.")
            
        self.chunks = chunks
        self.encoder = SentenceTransformer(model_name)
        
        # Xây dựng ma trận nhúng VectorDense Index
        raw_embeddings = self.encoder.encode(self.chunks, show_progress_bar=False)
        self.embeddings = np.array(raw_embeddings)
        
        # Xây dựng bộ chỉ mục từ khóa từ vựng tiếng Việt (BM25 Index)
        self.tokenized_corpus = [self._tokenize(doc) for doc in self.chunks]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def _tokenize(self, text: str) -> List[str]:
        # Tách từ cơ bản và loại bỏ các ký tự đặc biệt gây nhiễu chỉ mục
        clean = re.sub(r'[^\w\s]', ' ', text.lower())
        return [w for w in clean.split(' ') if w.strip()]

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # 1. Thực hiện tìm kiếm chuyên sâu bằng tương đồng Vector (Dense)
        query_vector = self.encoder.encode([query])[0]
        
        norm_matrix = np.linalg.norm(self.embeddings, axis=1)
        norm_query = np.linalg.norm(query_vector)
        
        # Thêm sai số epsilon 1e-9 ngăn chặn tuyệt đối lỗi hệ thống chia cho số 0
        denominator = norm_matrix * norm_query + 1e-9
        cosine_scores = np.dot(self.embeddings, query_vector) / denominator
        dense_ranks = np.argsort(cosine_scores)[::-1]
        
        # 2. Thực hiện tìm kiếm tần suất từ khóa chính xác (Sparse)
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(tokenized_query)
        sparse_ranks = np.argsort(bm25_scores)[::-1]
        
        # 3. Hợp nhất hai không gian điểm số bằng giải thuật Reciprocal Rank Fusion (RRF)
        rrf_scores = {}
        constant_k = 60 
        
        for rank, idx in enumerate(dense_ranks):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (constant_k + rank + 1)
            
        for rank, idx in enumerate(sparse_ranks):
            rrf_scores[idx] = rrf_scores.get(idx, 0.0) + 1.0 / (constant_k + rank + 1)
            
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        output_results = []
        for idx, score in sorted_docs[:top_k]:
            output_results.append({
                "text": self.chunks[idx],
                "rrf_score": float(score),
                "internal_id": idx
            })
        return output_results

def request_gemini_api(prompt: str, system_instruction: str = "") -> str:
    """Thực hiện kết nối và tạo sinh văn bản qua API Gateway của Google Gemini"""
    api_key = CONFIG["api_key"]
    if not api_key:
        return "[CẢNH BÁO]: Chưa cấu hình API Key. Hệ thống RAG dừng lại ở bước đóng gói Prompt."

    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{CONFIG['gemini_model']}:generateContent?key={api_key}"
    
    struct_payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    if system_instruction:
        struct_payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
    encoded_data = json.dumps(struct_payload).encode("utf-8")
    
    # Kỹ thuật thiết lập độ trễ lũy tiến tránh nghẽn băng thông hệ thống
    network_delays = [1, 3, 5]
    for step, delay in enumerate(network_delays):
        try:
            req = urllib.request.Request(
                endpoint, 
                data=encoded_data, 
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req) as response:
                response_decoded = json.loads(response.read().decode("utf-8"))
                return response_decoded["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as http_err:
            if step == len(network_delays) - 1:
                return f"Lỗi kết nối API Gateway: {http_err.read().decode('utf-8')}"
            time.sleep(delay)
        except Exception as general_err:
            if step == len(network_delays) - 1:
                return f"Lỗi hệ thống phát sinh: {str(general_err)}"
            time.sleep(delay)
    return "Mô hình không phản hồi."

def main():
    print("--- KHỞI CHẠY HỆ THỐNG BASELINE RAG HOÀN CHỈNH ---")
    
    # Kết nối và stream trực tiếp dữ liệu từ HuggingFace để tối ưu bộ nhớ máy chạy
    print("1. Đang kết nối luồng dữ liệu tới NTT-hil-insight/OpenDocVQA-Corpus...")
    try:
        hf_stream = load_dataset("NTT-hil-insight/OpenDocVQA-Corpus", split="train", streaming=True)
        # Trích xuất 5 tài liệu mẫu đầu tiên từ tập dữ liệu lớn phục vụ kiểm thử Baseline nhanh
        sample_data = list(hf_stream.take(5))
        
        extracted_texts = []
        for item in sample_data:
            # Tự động nhận diện cấu trúc trường dữ liệu văn bản linh hoạt
            for key in ['text', 'ocr', 'content', 'document_text']:
                if key in item and item[key]:
                    extracted_texts.append(str(item[key]))
                    break
        
        raw_corpus = "\n".join(extracted_texts)
    except Exception as e:
        print(f"Không thể kết nối trực tiếp HuggingFace ({e}). Chuyển hướng nạp dữ liệu cấu trúc cục bộ...")
        raw_corpus = (
            "Quy định của doanh nghiệp công nghệ số GreenNode năm 2026. "
            "Tất cả nhân sự chính thức được cấp quyền truy cập hạ tầng tính toán Cloud và cụm GPU Cluster. "
            "Thủ tục đăng ký tài khoản cần thông qua trưởng phòng kỹ thuật và phê duyệt bởi Giám đốc công nghệ (CTO). "
            "Thời gian xử lý cấp phát tài nguyên trong vòng 24 giờ làm việc kể từ khi nhận đủ biểu mẫu yêu cầu."
        )

    print("2. Tiến hành phân mảnh dữ liệu văn bản theo cấu trúc Word-based...")
    splitter = VietnameseWordSplitter(
        chunk_size=CONFIG["chunk_size_words"], 
        overlap=CONFIG["chunk_overlap_words"]
    )
    all_chunks = splitter.split_text(raw_corpus)
    print(f" -> Đã tạo thành công {len(all_chunks)} phân mảnh văn bản an toàn ngữ nghĩa.")

    print("3. Khởi tạo và nạp chỉ mục vào bộ tìm kiếm lai (Dense-Sparse Indexing)...")
    search_engine = ProductionHybridRetriever(all_chunks, CONFIG["embedding_model"])

    # Thiết lập câu hỏi kiểm thử hệ thống
    test_query = "Quy trình đăng ký tài khoản sử dụng cụm GPU và tài nguyên máy chủ được quy định như thế nào?"
    print(f"4. Nhận câu hỏi đầu vào: '{test_query}'")
    
    retrieved_packages = search_engine.retrieve(test_query, top_k=CONFIG["top_k"])
    
    print("\n--- CÁC PHÂN MẢNH TRÍCH XUẤT LIÊN QUAN NHẤT (HYBRID RETRIEVAL) ---")
    for pos, item in enumerate(retrieved_packages):
        print(f"Top [{pos+1}] Score (RRF): {item['rrf_score']:.5f} | Nội dung: {item['text'][:120]}...")
    print("-------------------------------------------------------------------\n")

    # Xây dựng prompt tích hợp ngữ cảnh thu được
    context_builder = "\n".join([f"- Ngữ cảnh trích xuất: {doc['text']}" for doc in retrieved_packages])
    
    system_role = (
        "Bạn là chuyên gia quản lý tri thức và điều hành thông tin nội bộ của doanh nghiệp. "
        "Hãy dùng hoàn toàn các thông tin ngữ cảnh được cung cấp dưới đây để đưa ra câu trả lời chính xác, "
        "ngắn gọn và đúng trọng tâm câu hỏi. Nếu thông tin không có trong ngữ cảnh, hãy phản hồi là không tìm thấy quy định."
    )
    
    final_prompt = f"""
    Dữ liệu ngữ cảnh hệ thống tìm được:
    {context_builder}
    
    Dựa trên dữ liệu trên, hãy giải đáp thắc mắc sau của nhân sự:
    Câu hỏi: {test_query}
    """

    print("5. Thực hiện gửi dữ liệu tổng hợp qua mô hình sinh ngôn ngữ...")
    rag_response = request_gemini_api(final_prompt, system_role)
    
    print("\n=== TRẢ LỜI CUỐI CÙNG TỪ HỆ THỐNG RAG ===")
    print(rag_response)
    print("=========================================\n")

if __name__ == "__main__":
    main()