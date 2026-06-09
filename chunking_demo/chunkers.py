"""
chunkers.py
-----------
Định nghĩa 3 chiến lược chunking cho văn bản tiếng Việt:
  1. Fixed Chunking      - CharacterTextSplitter
  2. Recursive Chunking  - RecursiveCharacterTextSplitter
  3. Semantic Chunking   - SemanticChunker (dựa trên embedding)
"""

from dataclasses import dataclass, field
from typing import List

from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter


# ─────────────────────────────────────────────
# Cấu trúc kết quả trả về cho mỗi chiến lược
# ─────────────────────────────────────────────
@dataclass
class ChunkResult:
    strategy_name: str
    chunks: List[str]
    total_chunks: int = field(init=False)

    def __post_init__(self):
        self.total_chunks = len(self.chunks)

    def preview(self, n: int = 2) -> List[str]:
        """Trả về n chunk đầu tiên để xem trước."""
        return self.chunks[:n]


# ─────────────────────────────────────────────
# 1. Fixed Chunking — CharacterTextSplitter
# ─────────────────────────────────────────────
def fixed_chunking(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> ChunkResult:
    """
    Chia văn bản theo số ký tự cố định.
    Đơn giản nhất, không quan tâm đến cấu trúc câu hay ngữ nghĩa.
    """
    splitter = CharacterTextSplitter(
        separator="\n",          # Ưu tiên tách theo dòng mới
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=False,
    )
    chunks = splitter.split_text(text)
    return ChunkResult(strategy_name="Fixed (CharacterTextSplitter)", chunks=chunks)


# ─────────────────────────────────────────────
# 2. Recursive Chunking — RecursiveCharacterTextSplitter
# ─────────────────────────────────────────────
def recursive_chunking(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> ChunkResult:
    """
    Chia văn bản đệ quy theo danh sách separator ưu tiên:
    ["\n\n", "\n", ". ", " ", ""]
    Giúp giữ nguyên cấu trúc đoạn văn và câu tốt hơn Fixed Chunking.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        # Separator phù hợp cho văn bản tiếng Việt
        separators=["\n\n", "\n", ".", "!", "?", " ", ""],
    )
    chunks = splitter.split_text(text)
    return ChunkResult(strategy_name="Recursive (RecursiveCharacterTextSplitter)", chunks=chunks)


# ─────────────────────────────────────────────
# 3. Semantic Chunking — SemanticChunker
# ─────────────────────────────────────────────
def semantic_chunking(text: str, embeddings) -> ChunkResult:
    """
    Chia văn bản dựa trên sự thay đổi ngữ nghĩa giữa các câu.
    Sử dụng embedding để đo cosine similarity và phát hiện breakpoint.
    Yêu cầu truyền vào một embeddings model đã khởi tạo sẵn.
    """
    # Import ở đây để tránh lỗi nếu langchain_experimental chưa cài
    try:
        from langchain_experimental.text_splitter import SemanticChunker
    except ImportError:
        raise ImportError(
            "Thiếu thư viện: pip install langchain-experimental"
        )

    splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",  # Dùng phương pháp percentile (phổ biến nhất)
        breakpoint_threshold_amount=95,          # Ngưỡng 95th percentile
    )
    chunks = splitter.split_text(text)
    return ChunkResult(strategy_name="Semantic (SemanticChunker + SBERT)", chunks=chunks)
