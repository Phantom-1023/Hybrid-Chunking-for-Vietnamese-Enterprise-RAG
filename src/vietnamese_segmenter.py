"""
Vietnamese Word Segmentation Module
Phân đoạn từ tiếng Việt để tối ưu cho embedding
"""

from typing import List, Dict, Any, Optional
from src.utils import setup_logger

logger = setup_logger(__name__)


class VietnameseSegmenter:
    """Phân đoạn từ tiếng Việt"""
    
    def __init__(self, use_underthesea: bool = True):
        """
        Khởi tạo VietnameseSegmenter
        
        Args:
            use_underthesea: Sử dụng Underthesea nếu có sẵn
        """
        self.logger = logger
        self.use_underthesea = use_underthesea
        self.underthesea_available = False
        
        # Cố gắng import Underthesea
        if use_underthesea:
            try:
                import underthesea
                self.underthesea = underthesea
                self.underthesea_available = True
                self.logger.info("✅ Underthesea library available")
            except ImportError:
                self.logger.warning("⚠️  Underthesea not available. Using fallback method.")
                self.underthesea_available = False
    
    def segment_text(self, text: str) -> str:
        """
        Phân đoạn từ trong văn bản
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Văn bản đã phân đoạn (các từ được tách bằng dấu cách)
        """
        if not text:
            return ""
        
        if self.underthesea_available:
            return self._segment_with_underthesea(text)
        else:
            return self._segment_fallback(text)
    
    def _segment_with_underthesea(self, text: str) -> str:
        """
        Phân đoạn sử dụng Underthesea
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Văn bản đã phân đoạn
        """
        try:
            # Sử dụng word_tokenize từ Underthesea
            from underthesea import word_tokenize
            
            # Chia thành câu trước
            sentences = text.split('.')
            segmented_sentences = []
            
            for sentence in sentences:
                if sentence.strip():
                    # Phân đoạn từ
                    tokens = word_tokenize(sentence)
                    segmented_sentences.append(' '.join(tokens))
            
            return '. '.join(segmented_sentences)
            
        except Exception as e:
            self.logger.warning(f"Lỗi phân đoạn với Underthesea: {str(e)}")
            return self._segment_fallback(text)
    
    def _segment_fallback(self, text: str) -> str:
        """
        Phân đoạn sử dụng phương pháp fallback (dựa trên regex)
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Văn bản đã phân đoạn
        """
        import re
        
        # Danh sách các từ ghép tiếng Việt phổ biến
        compound_words = {
            'thành phố': 'thành_phố',
            'công ty': 'công_ty',
            'nhân viên': 'nhân_viên',
            'lương cơ bản': 'lương_cơ_bản',
            'bảo hiểm': 'bảo_hiểm',
            'hợp đồng': 'hợp_đồng',
            'quy định': 'quy_định',
            'chính sách': 'chính_sách',
            'phúc lợi': 'phúc_lợi',
            'nghỉ phép': 'nghỉ_phép',
            'giờ làm việc': 'giờ_làm_việc',
            'trực tiếp': 'trực_tiếp',
            'quản lý': 'quản_lý',
            'kinh doanh': 'kinh_doanh',
            'tài chính': 'tài_chính',
            'báo cáo': 'báo_cáo',
            'dữ liệu': 'dữ_liệu',
            'hệ thống': 'hệ_thống',
            'công nghệ': 'công_nghệ',
            'phát triển': 'phát_triển',
        }
        
        # Thay thế từ ghép bằng phiên bản có dấu gạch dưới
        result = text
        for compound, replacement in compound_words.items():
            result = re.sub(r'\b' + compound + r'\b', replacement, result, flags=re.IGNORECASE)
        
        return result
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tách văn bản thành các token (từ)
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Danh sách các token
        """
        if self.underthesea_available:
            try:
                from underthesea import word_tokenize
                return word_tokenize(text)
            except Exception as e:
                self.logger.warning(f"Lỗi tokenize: {str(e)}")
        
        # Fallback: chia đơn giản theo khoảng trắng
        return text.split()
    
    def pos_tag(self, text: str) -> List[tuple]:
        """
        Gán nhãn từ loại (Part-of-Speech tagging)
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Danh sách tuple (token, pos_tag)
        """
        if self.underthesea_available:
            try:
                from underthesea import pos_tag
                return pos_tag(text)
            except Exception as e:
                self.logger.warning(f"Lỗi POS tagging: {str(e)}")
        
        # Fallback: chỉ trả về tokens mà không có tag
        tokens = self.tokenize(text)
        return [(token, 'NN') for token in tokens]
    
    def named_entity_recognition(self, text: str) -> List[Dict[str, Any]]:
        """
        Nhận dạng các thực thể được đặt tên (Named Entity Recognition)
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Danh sách các thực thể được nhận dạng
        """
        if self.underthesea_available:
            try:
                from underthesea import ner
                entities = ner(text)
                return [
                    {
                        'text': entity[0],
                        'type': entity[1],
                        'start': text.find(entity[0]),
                        'end': text.find(entity[0]) + len(entity[0])
                    }
                    for entity in entities
                ]
            except Exception as e:
                self.logger.warning(f"Lỗi NER: {str(e)}")
        
        return []
    
    def dependency_parse(self, text: str) -> Dict[str, Any]:
        """
        Phân tích cú pháp phụ thuộc (Dependency Parsing)
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Cây phân tích cú pháp
        """
        if self.underthesea_available:
            try:
                from underthesea import parse
                return parse(text)
            except Exception as e:
                self.logger.warning(f"Lỗi dependency parsing: {str(e)}")
        
        return {}


class SegmentedChunk:
    """Chunk đã được phân đoạn từ"""
    
    def __init__(self, original_content: str, segmented_content: str, 
                 chunk_id: str, source_document: str = "unknown",
                 chunk_index: int = 0, start_char: int = 0,
                 end_char: int = 0, metadata: Optional[Dict[str, Any]] = None):
        """
        Khởi tạo SegmentedChunk
        
        Args:
            original_content: Nội dung gốc
            segmented_content: Nội dung đã phân đoạn
            chunk_id: ID của chunk
            metadata: Metadata bổ sung
        """
        self.original_content = original_content
        self.content = original_content
        self.segmented_content = segmented_content
        self.chunk_id = chunk_id
        self.source_document = source_document
        self.chunk_index = chunk_index
        self.start_char = start_char
        self.end_char = end_char
        self.metadata = metadata or {}
    
    def __repr__(self) -> str:
        return f"SegmentedChunk(id='{self.chunk_id}', size={len(self.segmented_content)})"


class ChunkSegmenter:
    """Phân đoạn các chunks"""
    
    def __init__(self, use_underthesea: bool = True):
        """
        Khởi tạo ChunkSegmenter
        
        Args:
            use_underthesea: Sử dụng Underthesea
        """
        self.segmenter = VietnameseSegmenter(use_underthesea)
        self.logger = logger
    
    def segment_chunks(self, chunks: List[Any]) -> List[SegmentedChunk]:
        """
        Phân đoạn danh sách chunks
        
        Args:
            chunks: Danh sách Chunk objects
            
        Returns:
            Danh sách SegmentedChunk objects
        """
        segmented_chunks = []
        
        for chunk in chunks:
            try:
                # Phân đoạn nội dung
                segmented_content = self.segmenter.segment_text(chunk.content)
                
                # Tạo SegmentedChunk
                seg_chunk = SegmentedChunk(
                    original_content=chunk.content,
                    segmented_content=segmented_content,
                    chunk_id=chunk.chunk_id,
                    source_document=getattr(chunk, "source_document", "unknown"),
                    chunk_index=getattr(chunk, "chunk_index", 0),
                    start_char=getattr(chunk, "start_char", 0),
                    end_char=getattr(chunk, "end_char", 0),
                    metadata=chunk.metadata
                )
                
                segmented_chunks.append(seg_chunk)
                
            except Exception as e:
                self.logger.error(f"Lỗi phân đoạn chunk {chunk.chunk_id}: {str(e)}")
        
        self.logger.info(f"✅ Phân đoạn {len(segmented_chunks)}/{len(chunks)} chunks")
        return segmented_chunks
    
    def get_segmentation_statistics(self, segmented_chunks: List[SegmentedChunk]) -> Dict[str, Any]:
        """
        Lấy thống kê về phân đoạn
        
        Args:
            segmented_chunks: Danh sách SegmentedChunk objects
            
        Returns:
            Dictionary với thống kê
        """
        if not segmented_chunks:
            return {
                'total_chunks': 0,
                'total_original_chars': 0,
                'total_segmented_chars': 0,
                'average_expansion': 0,
            }
        
        original_chars = sum(len(c.original_content) for c in segmented_chunks)
        segmented_chars = sum(len(c.segmented_content) for c in segmented_chunks)
        
        return {
            'total_chunks': len(segmented_chunks),
            'total_original_chars': original_chars,
            'total_segmented_chars': segmented_chars,
            'average_expansion': segmented_chars / original_chars if original_chars > 0 else 0,
        }
