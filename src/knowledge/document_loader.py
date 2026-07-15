from datasets import load_dataset
from src.knowledge.text_splitter import chunk_documents
from src.memory.vector_store import VectorStore
import traceback

def load_huggingface_data():
    all_texts = []
    print("🚀 Đang tải dữ liệu từ HuggingFace...")
    
    # 1. Pháp lý VN (NamSyntax)
    try:
        ds_legal = load_dataset("NamSyntax/Vietnamese-Legal-QA-RAG", split="train")
        for row in ds_legal:
            # Gom toàn bộ nội dung của các cột thành 1 khối text để chắc chắn không trượt cột nào
            text_content = " ".join([str(val) for val in row.values() if val])
            if text_content.strip():
                all_texts.append(text_content)
        print(f"✅ Tải thành công {len(ds_legal)} mẫu từ Legal-QA")
    except Exception as e:
        print(f"❌ Lỗi tải Legal-QA: {e}")

    # 2. Vietnamese RAG
    try:
        ds_rag = load_dataset("sailor2/Vietnamese_RAG", split="train[:200]")
        for row in ds_rag:
            text_content = " ".join([str(val) for val in row.values() if val])
            if text_content.strip():
                all_texts.append(text_content)
        print(f"✅ Tải thành công {len(ds_rag)} mẫu từ Vietnamese_RAG")
    except Exception as e:
        print(f"❌ Lỗi tải Vietnamese_RAG: {e}")

    if len(all_texts) == 0:
        print("⚠️ CẢNH BÁO: KHÔNG CÓ DATA NÀO ĐƯỢC TẢI VỀ! HÃY KIỂM TRA LẠI MẠNG HOẶC HUGGINGFACE TOKEN.")
        return

    print(f"📦 Đã thu thập được {len(all_texts)} tài liệu gốc. Đang tiến hành băm nhỏ (Chunking)...")
    chunks = chunk_documents(all_texts)
    
    print("⚙️ Đang kết nối Qdrant và tiến hành Embedding...")
    db = VectorStore()
    db.ingest(chunks)
    print("🎉 NẠP DỮ LIỆU THÀNH CÔNG VÀO HỆ THỐNG!")

if __name__ == "__main__":
    load_huggingface_data()