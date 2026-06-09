"""
main.py
-------
Pipeline demo 3 chiến lược Chunking trên dataset tiếng Việt.
Dataset: sailor2/Vietnamese_RAG (HuggingFace)
Chỉ tải 5 document đầu tiên bằng streaming=True để tiết kiệm thời gian.

Chạy: python main.py
"""

import textwrap
import warnings
warnings.filterwarnings("ignore")  # Tắt cảnh báo không cần thiết

# ─────────────────────────────────────────────
# Bước 1: Tải dataset từ HuggingFace (chỉ 5 documents)
# ─────────────────────────────────────────────
def load_vietnamese_documents(num_docs: int = 5) -> list[str]:
    """
    Tải num_docs document đầu tiên từ sailor2/Vietnamese_RAG.
    Dùng streaming=True để KHÔNG tải toàn bộ dataset về máy.

    Schema thực tế của dataset:
      - question: str
      - answer:   str
      - context:  List[str]  ← 5 đoạn văn ngữ cảnh dạng list, KHÔNG phải str

    Chiến lược lấy text: nối toàn bộ 5 context passages của mỗi sample
    thành 1 document dài để demo chunking có ý nghĩa hơn.
    """
    print(f" Đang tải {num_docs} document đầu tiên từ HuggingFace...")
    from datasets import load_dataset

    # streaming=True: chỉ tải từng batch khi cần, không download toàn bộ
    # Dùng config "BKAI_RAG" — subset lớn nhất, ổn định nhất
    dataset = load_dataset(
        "sailor2/Vietnamese_RAG",
        "BKAI_RAG",             # Config: BKAI_RAG | LegalRAG | expert | viQuAD
        split="train",
        streaming=True,
    )

    documents = []
    for i, sample in enumerate(dataset):
        if i >= num_docs:
            break

        # Cột "context" là List[str] với 5 đoạn văn, nối lại thành 1 document
        context_list = sample.get("context", [])
        if isinstance(context_list, list) and context_list:
            # Nối các đoạn bằng dấu xuống dòng kép để chunker nhận biết ranh giới
            text = "\n\n".join(c.strip() for c in context_list if c.strip())
        else:
            # Fallback: thử lấy answer nếu context không có
            text = sample.get("answer", "").strip()

        if text:
            documents.append(text)

    print(f"✅ Tải thành công {len(documents)} documents.\n")
    return documents


# ─────────────────────────────────────────────
# Bước 2: Khởi tạo Embedding Model (dùng cho Semantic Chunking)
# ─────────────────────────────────────────────
def load_embedding_model():
    """
    Khởi tạo sentence-transformer để dùng trong SemanticChunker.
    Dùng 'keepitreal/vietnamese-sbert' vì nhẹ hơn BAAI/bge-m3 (~90MB vs ~2GB).
    Nếu muốn chất lượng tốt hơn, đổi thành 'BAAI/bge-m3'.
    """
    print(" Đang tải embedding model (vietnamese-sbert)...")
    from langchain_huggingface import HuggingFaceEmbeddings

    embeddings = HuggingFaceEmbeddings(
        model_name="keepitreal/vietnamese-sbert",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print("✅ Embedding model đã sẵn sàng.\n")
    return embeddings


# ─────────────────────────────────────────────
# Bước 3: In kết quả ra console
# ─────────────────────────────────────────────
def print_results(result, preview_n: int = 2):
    """In thống kê và xem trước chunk cho một chiến lược."""
    SEPARATOR = "=" * 65
    THIN_SEP  = "-" * 65

    print(SEPARATOR)
    print(f"   Chiến lược: {result.strategy_name}")
    print(f"   Tổng số chunks: {result.total_chunks}")
    print(THIN_SEP)

    previews = result.preview(preview_n)
    for idx, chunk in enumerate(previews, start=1):
        # Wrap text cho dễ đọc trên console
        wrapped = textwrap.fill(chunk, width=62, subsequent_indent="     ")
        print(f"  [Chunk {idx}]")
        print(f"  Độ dài: {len(chunk)} ký tự")
        print(f"  Nội dung:")
        # In từng dòng với indent
        for line in wrapped.splitlines():
            print(f"     {line}")
        if idx < len(previews):
            print()

    print(SEPARATOR)
    print()


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
def main():
    print("\n" + "=" * 65)
    print("   🇻🇳  DEMO CHUNKING STRATEGIES — VIETNAMESE RAG PIPELINE")
    print("=" * 65 + "\n")

    # 1. Load dataset (chỉ 5 docs, dùng streaming)
    documents = load_vietnamese_documents(num_docs=5)

    if not documents:
        print("❌ Không lấy được document nào từ dataset. Vui lòng kiểm tra kết nối.")
        return

    # Chọn document đầu tiên để demo
    demo_text = documents[0]
    print(f" Document được chọn để demo:")
    print(f"   Độ dài: {len(demo_text)} ký tự")
    print(f"   Preview: {demo_text[:120].replace(chr(10), ' ')}...")
    print()

    # 2. Load embedding model
    embeddings = load_embedding_model()

    # 3. Import các chunker
    from chunkers import fixed_chunking, recursive_chunking, semantic_chunking

    print(" Bắt đầu chạy 3 chiến lược chunking...\n")

    # ── Chiến lược 1: Fixed Chunking ──
    print(" [1/3] Đang chạy Fixed Chunking...")
    result_fixed = fixed_chunking(demo_text, chunk_size=500, chunk_overlap=50)
    print_results(result_fixed, preview_n=2)

    # ── Chiến lược 2: Recursive Chunking ──
    print(" [2/3] Đang chạy Recursive Chunking...")
    result_recursive = recursive_chunking(demo_text, chunk_size=500, chunk_overlap=50)
    print_results(result_recursive, preview_n=2)

    # ── Chiến lược 3: Semantic Chunking ──
    print(" [3/3] Đang chạy Semantic Chunking ")
    result_semantic = semantic_chunking(demo_text, embeddings=embeddings)
    print_results(result_semantic, preview_n=2)

    # ── Bảng tổng hợp kết quả ──
    print("=" * 65)
    print("   BẢNG TỔNG HỢP KẾT QUẢ")
    print("=" * 65)
    print(f"  {'Chiến lược':<42} {'Tổng chunks':>10}")
    print("-" * 65)
    for result in [result_fixed, result_recursive, result_semantic]:
        name = result.strategy_name[:42]
        print(f"  {name:<42} {result.total_chunks:>10}")
    print("=" * 65)
    print("\n✅ Demo hoàn tất! \n")


if __name__ == "__main__":
    main()
