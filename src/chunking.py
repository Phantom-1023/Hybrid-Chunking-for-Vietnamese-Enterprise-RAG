"""
Text Chunking Module
Chia nhỏ tài liệu thành các chunks tối ưu cho embedding
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from src.utils import setup_logger

logger = setup_logger(__name__)


@dataclass
class Chunk:
    """Đại diện cho một chunk của tài liệu"""
    
    content: str
    chunk_id: str
    source_document: str
    start_char: int
    end_char: int
    chunk_index: int
    metadata: Dict[str, Any]
    
    def __repr__(self) -> str:
        return f"Chunk(id='{self.chunk_id}', size={len(self.content)}, doc='{self.source_document}')"


class TextChunker:
    """Chia nhỏ văn bản thành chunks"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Khởi tạo TextChunker
        
        Args:
            chunk_size: Kích thước mỗi chunk (số ký tự)
            chunk_overlap: Độ chồng lấp giữa các chunks (số ký tự)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.logger = logger
        
        if chunk_overlap >= chunk_size:
            self.logger.warning(f"chunk_overlap ({chunk_overlap}) >= chunk_size ({chunk_size})")
    
    def chunk_text(self, text: str, source_document: str = "unknown", 
                   metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        Chia văn bản thành chunks
        
        Args:
            text: Văn bản cần chia
            source_document: Tên tài liệu nguồn
            metadata: Metadata bổ sung
            
        Returns:
            Danh sách Chunk objects
        """
        if not text or len(text.strip()) == 0:
            self.logger.warning(f"Văn bản trống từ {source_document}")
            return []
        
        chunks = []
        chunk_index = 0
        start_char = 0
        
        while start_char < len(text):
            # Xác định vị trí kết thúc của chunk
            end_char = min(start_char + self.chunk_size, len(text))
            
            # Nếu không phải chunk cuối cùng, cố gắng chia tại ranh giới từ/câu
            if end_char < len(text):
                # Tìm vị trí tốt nhất để chia (dấu câu hoặc khoảng trắng)
                best_split = self._find_best_split_point(text, start_char, end_char)
                # Đảm bảo tiến bộ (tránh infinite loop)
                if best_split > start_char:
                    end_char = best_split
            
            # Trích xuất chunk
            chunk_text = text[start_char:end_char].strip()
            
            if chunk_text:  # Chỉ thêm nếu chunk không trống
                chunk_id = f"{source_document}_chunk_{chunk_index}"
                
                chunk = Chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    source_document=source_document,
                    start_char=start_char,
                    end_char=end_char,
                    chunk_index=chunk_index,
                    metadata=metadata or {}
                )
                
                chunks.append(chunk)
                chunk_index += 1

            if end_char >= len(text):
                break
            
            # Di chuyển tới chunk tiếp theo (với overlap)
            # Đảm bảo luôn tiến bộ
            if end_char <= start_char:
                # Nếu không có tiến bộ, bỏ qua một phần
                start_char = start_char + max(1, self.chunk_size // 2)
            else:
                next_start = end_char - self.chunk_overlap
                start_char = next_start if next_start > start_char else end_char
        
        self.logger.info(f"✅ Chia '{source_document}' thành {len(chunks)} chunks")
        return chunks
    
    def _find_best_split_point(self, text: str, start: int, end: int) -> int:
        """
        Tìm vị trí tốt nhất để chia (tại dấu câu hoặc khoảng trắng)
        
        Args:
            text: Văn bản
            start: Vị trí bắt đầu
            end: Vị trí kết thúc gợi ý
            
        Returns:
            Vị trí tốt nhất để chia
        """
        # Ưu tiên: dấu câu (. ! ?)
        for i in range(end - 1, start, -1):
            if i < len(text) and text[i] in '.!?':
                return i + 1
        
        # Thứ hai: dấu phẩy hoặc dấu chấm phẩy
        for i in range(end - 1, start, -1):
            if i < len(text) and text[i] in ',;':
                return i + 1
        
        # Thứ ba: khoảng trắng
        for i in range(end - 1, start, -1):
            if i < len(text) and text[i].isspace():
                return i
        
        # Nếu không tìm được, trả về vị trí kết thúc
        return end
    
    def chunk_documents(self, documents: List[Any]) -> List[Chunk]:
        """
        Chia nhỏ danh sách tài liệu
        
        Args:
            documents: Danh sách Document objects
            
        Returns:
            Danh sách Chunk objects
        """
        all_chunks = []
        
        for doc in documents:
            chunks = self.chunk_text(
                text=doc.content,
                source_document=doc.filename,
                metadata={
                    'file_type': doc.file_type,
                    'file_size': doc.file_size,
                    'loaded_at': doc.loaded_at,
                }
            )
            all_chunks.extend(chunks)
        
        self.logger.info(f"✅ Tổng cộng {len(all_chunks)} chunks từ {len(documents)} tài liệu")
        return all_chunks
    
    def get_chunk_statistics(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """
        Lấy thống kê về chunks
        
        Args:
            chunks: Danh sách chunks
            
        Returns:
            Dictionary với thống kê
        """
        if not chunks:
            return {
                'total_chunks': 0,
                'total_characters': 0,
                'average_chunk_size': 0,
                'min_chunk_size': 0,
                'max_chunk_size': 0,
            }
        
        sizes = [len(chunk.content) for chunk in chunks]
        
        return {
            'total_chunks': len(chunks),
            'total_characters': sum(sizes),
            'average_chunk_size': sum(sizes) / len(chunks),
            'min_chunk_size': min(sizes),
            'max_chunk_size': max(sizes),
            'documents': len(set(chunk.source_document for chunk in chunks)),
        }


class ParentChildChunker:
    """Create large parent chunks for context and smaller child chunks for embedding search."""

    def __init__(
        self,
        parent_chunk_size: int = 2200,
        parent_chunk_overlap: int = 200,
        child_chunk_size: int = 500,
        child_chunk_overlap: int = 80,
    ):
        self.parent_chunker = TextChunker(parent_chunk_size, parent_chunk_overlap)
        self.child_chunker = TextChunker(child_chunk_size, child_chunk_overlap)
        self.logger = logger

    def chunk_text(
        self,
        text: str,
        source_document: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        parent_chunks = self.parent_chunker.chunk_text(
            text=text,
            source_document=source_document,
            metadata={**(metadata or {}), "chunk_level": "parent"},
        )
        child_chunks: List[Chunk] = []

        for parent in parent_chunks:
            parent_id = parent.chunk_id.replace("_chunk_", "_parent_")
            children = self.child_chunker.chunk_text(
                text=parent.content,
                source_document=source_document,
                metadata={
                    **(metadata or {}),
                    "chunk_level": "child",
                    "parent_id": parent_id,
                    "parent_content": parent.content,
                    "parent_start_char": parent.start_char,
                    "parent_end_char": parent.end_char,
                },
            )

            for local_index, child in enumerate(children):
                child.chunk_id = f"{parent_id}_child_{local_index}"
                child.start_char = parent.start_char + child.start_char
                child.end_char = parent.start_char + child.end_char
                child.chunk_index = len(child_chunks)
                child.metadata.update(
                    {
                        "parent_id": parent_id,
                        "parent_chunk_index": parent.chunk_index,
                        "child_index_in_parent": local_index,
                    }
                )
                child_chunks.append(child)

        self.logger.info(
            f"✅ Parent-child chunking produced {len(parent_chunks)} parents and {len(child_chunks)} children for '{source_document}'"
        )
        return child_chunks

    def chunk_documents(self, documents: List[Any]) -> List[Chunk]:
        all_chunks: List[Chunk] = []
        for doc in documents:
            chunks = self.chunk_text(
                text=doc.content,
                source_document=doc.filename,
                metadata={
                    "file_type": doc.file_type,
                    "file_size": doc.file_size,
                    "loaded_at": doc.loaded_at,
                    **doc.metadata,
                },
            )
            all_chunks.extend(chunks)
        return all_chunks


class SentenceChunker:
    """Chia văn bản theo câu"""
    
    def __init__(self, sentences_per_chunk: int = 3, sentence_overlap: int = 1):
        """
        Khởi tạo SentenceChunker
        
        Args:
            sentences_per_chunk: Số câu mỗi chunk
            sentence_overlap: Số câu chồng lấp
        """
        self.sentences_per_chunk = sentences_per_chunk
        self.sentence_overlap = sentence_overlap
        self.logger = logger
    
    def chunk_text(self, text: str, source_document: str = "unknown",
                   metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        Chia văn bản theo câu
        
        Args:
            text: Văn bản cần chia
            source_document: Tên tài liệu nguồn
            metadata: Metadata bổ sung
            
        Returns:
            Danh sách Chunk objects
        """
        import re
        
        # Chia thành câu
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return []
        
        chunks = []
        chunk_index = 0
        
        for i in range(0, len(sentences), self.sentences_per_chunk - self.sentence_overlap):
            # Xác định câu bắt đầu và kết thúc
            start_idx = max(0, i - self.sentence_overlap)
            end_idx = min(len(sentences), i + self.sentences_per_chunk)
            
            # Kết hợp các câu
            chunk_text = ' '.join(sentences[start_idx:end_idx])
            
            if chunk_text:
                chunk_id = f"{source_document}_sent_chunk_{chunk_index}"
                
                chunk = Chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    source_document=source_document,
                    start_char=0,
                    end_char=0,
                    chunk_index=chunk_index,
                    metadata=metadata or {}
                )
                
                chunks.append(chunk)
                chunk_index += 1
        
        self.logger.info(f"✅ Chia '{source_document}' thành {len(chunks)} sentence chunks")
        return chunks


class ParagraphChunker:
    """Chia văn bản theo đoạn"""
    
    def __init__(self, paragraphs_per_chunk: int = 2, paragraph_overlap: int = 0):
        """
        Khởi tạo ParagraphChunker
        
        Args:
            paragraphs_per_chunk: Số đoạn mỗi chunk
            paragraph_overlap: Số đoạn chồng lấp
        """
        self.paragraphs_per_chunk = paragraphs_per_chunk
        self.paragraph_overlap = paragraph_overlap
        self.logger = logger
    
    def chunk_text(self, text: str, source_document: str = "unknown",
                   metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        Chia văn bản theo đoạn
        
        Args:
            text: Văn bản cần chia
            source_document: Tên tài liệu nguồn
            metadata: Metadata bổ sung
            
        Returns:
            Danh sách Chunk objects
        """
        import re
        
        # Chia thành đoạn (phân cách bằng dòng trống)
        paragraphs = re.split(r'\n\n+', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        chunk_index = 0
        
        for i in range(0, len(paragraphs), self.paragraphs_per_chunk - self.paragraph_overlap):
            # Xác định đoạn bắt đầu và kết thúc
            start_idx = max(0, i - self.paragraph_overlap)
            end_idx = min(len(paragraphs), i + self.paragraphs_per_chunk)
            
            # Kết hợp các đoạn
            chunk_text = '\n\n'.join(paragraphs[start_idx:end_idx])
            
            if chunk_text:
                chunk_id = f"{source_document}_para_chunk_{chunk_index}"
                
                chunk = Chunk(
                    content=chunk_text,
                    chunk_id=chunk_id,
                    source_document=source_document,
                    start_char=0,
                    end_char=0,
                    chunk_index=chunk_index,
                    metadata=metadata or {}
                )
                
                chunks.append(chunk)
                chunk_index += 1
        
        self.logger.info(f"✅ Chia '{source_document}' thành {len(chunks)} paragraph chunks")
        return chunks


class RecursiveChunker:
    """Split text recursively by increasingly small separators."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = ["\n\n", "\n", ". ", " ", ""]
        self.logger = logger

    def chunk_text(
        self,
        text: str,
        source_document: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        if not text or not text.strip():
            return []

        raw_chunks = self._split_recursive(text.strip(), self.separators)
        merged_chunks = self._merge_chunks(raw_chunks)
        chunks: List[Chunk] = []
        search_start = 0

        for index, content in enumerate(merged_chunks):
            start_char = text.find(content[: min(30, len(content))], search_start)
            if start_char < 0:
                start_char = search_start
            end_char = min(start_char + len(content), len(text))
            search_start = end_char
            chunks.append(
                Chunk(
                    content=content,
                    chunk_id=f"{source_document}_recursive_chunk_{index}",
                    source_document=source_document,
                    start_char=start_char,
                    end_char=end_char,
                    chunk_index=index,
                    metadata={**(metadata or {}), "strategy": "recursive"},
                )
            )

        self.logger.info(f"Recursive chunking produced {len(chunks)} chunks for '{source_document}'")
        return chunks

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            step = max(1, self.chunk_size - self.chunk_overlap)
            return [text[index:index + self.chunk_size] for index in range(0, len(text), step)]

        pieces = text.split(separator)
        if len(pieces) == 1:
            return self._split_recursive(text, remaining_separators)

        chunks: List[str] = []
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            if separator == ". ":
                piece = piece + "."
            if len(piece) > self.chunk_size and remaining_separators:
                chunks.extend(self._split_recursive(piece, remaining_separators))
            else:
                chunks.append(piece)
        return chunks

    def _merge_chunks(self, pieces: List[str]) -> List[str]:
        chunks: List[str] = []
        current = ""

        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue

            candidate = f"{current} {piece}".strip() if current else piece
            if len(candidate) <= self.chunk_size:
                current = candidate
                continue

            if current:
                chunks.append(current)
            current = piece

        if current:
            chunks.append(current)

        if not chunks and pieces:
            return [pieces[0][:self.chunk_size]]
        return chunks


class SemanticChunker:
    """Lightweight semantic strategy placeholder with an explicit fallback."""

    def __init__(self, sentences_per_chunk: int = 4, sentence_overlap: int = 1):
        self.fallback_chunker = SentenceChunker(
            sentences_per_chunk=sentences_per_chunk,
            sentence_overlap=sentence_overlap,
        )
        self.logger = logger

    def chunk_text(
        self,
        text: str,
        source_document: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Chunk]:
        chunks = self.fallback_chunker.chunk_text(
            text=text,
            source_document=source_document,
            metadata={
                **(metadata or {}),
                "strategy": "semantic",
                "semantic_fallback_used": True,
            },
        )

        if not chunks and text.strip():
            chunks = TextChunker(chunk_size=500, chunk_overlap=50).chunk_text(
                text=text,
                source_document=source_document,
                metadata={
                    **(metadata or {}),
                    "strategy": "semantic",
                    "semantic_fallback_used": True,
                },
            )

        for index, chunk in enumerate(chunks):
            chunk.chunk_id = f"{source_document}_semantic_chunk_{index}"
            chunk.chunk_index = index
            chunk.metadata["strategy"] = "semantic"
            chunk.metadata["semantic_fallback_used"] = True

        self.logger.info(f"Semantic fallback chunking produced {len(chunks)} chunks for '{source_document}'")
        return chunks


def chunk_text_by_strategy(
    strategy: str,
    text: str,
    source_document: str = "verify_sample",
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Chunk]:
    """Run one mission chunking strategy by name."""
    if strategy == "fixed":
        return TextChunker(chunk_size=500, chunk_overlap=50).chunk_text(
            text,
            source_document,
            {**(metadata or {}), "strategy": "fixed"},
        )
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=500, chunk_overlap=50).chunk_text(
            text,
            source_document,
            metadata,
        )
    if strategy == "semantic":
        return SemanticChunker().chunk_text(text, source_document, metadata)
    if strategy == "paragraph":
        return ParagraphChunker(paragraphs_per_chunk=2, paragraph_overlap=0).chunk_text(
            text,
            source_document,
            {**(metadata or {}), "strategy": "paragraph"},
        )
    raise ValueError(f"Unsupported chunking strategy: {strategy}")


class HybridChunker:
    """Kết hợp nhiều chiến lược chunking"""
    
    def __init__(self, primary_strategy: str = "character", 
                 chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Khởi tạo HybridChunker
        
        Args:
            primary_strategy: Chiến lược chính ("character", "sentence", "paragraph")
            chunk_size: Kích thước chunk (cho character strategy)
            chunk_overlap: Độ chồng lấp
        """
        self.primary_strategy = primary_strategy
        self.text_chunker = TextChunker(chunk_size, chunk_overlap)
        self.sentence_chunker = SentenceChunker()
        self.paragraph_chunker = ParagraphChunker()
        self.logger = logger
    
    def chunk_text(self, text: str, source_document: str = "unknown",
                   metadata: Optional[Dict[str, Any]] = None) -> List[Chunk]:
        """
        Chia văn bản sử dụng chiến lược chính
        
        Args:
            text: Văn bản cần chia
            source_document: Tên tài liệu nguồn
            metadata: Metadata bổ sung
            
        Returns:
            Danh sách Chunk objects
        """
        if self.primary_strategy == "character":
            return self.text_chunker.chunk_text(text, source_document, metadata)
        elif self.primary_strategy == "sentence":
            return self.sentence_chunker.chunk_text(text, source_document, metadata)
        elif self.primary_strategy == "paragraph":
            return self.paragraph_chunker.chunk_text(text, source_document, metadata)
        else:
            self.logger.error(f"Chiến lược không được hỗ trợ: {self.primary_strategy}")
            return []
