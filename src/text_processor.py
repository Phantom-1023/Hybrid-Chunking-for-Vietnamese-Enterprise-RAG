"""
Text Processor Module
Xử lý và làm sạch văn bản tiếng Việt
"""

import re
import unicodedata
from typing import List, Dict, Any, Optional
from src.utils import setup_logger, sanitize_text

logger = setup_logger(__name__)


class TextProcessor:
    """Xử lý và làm sạch văn bản"""
    
    # Các ký tự đặc biệt cần loại bỏ
    SPECIAL_CHARS_PATTERN = r'[^\w\s\u0100-\u01B0\u1E00-\u1EFF\.\,\!\?\;\:\-\(\)\"\']'
    
    # Các ký tự khoảng trắng
    WHITESPACE_PATTERN = r'\s+'
    
    # Các từ dừng tiếng Việt
    VIETNAMESE_STOPWORDS = {
        'và', 'hoặc', 'nhưng', 'tuy', 'vì', 'do', 'nếu', 'thì', 'khi', 'mà',
        'là', 'cái', 'chiếc', 'những', 'các', 'của', 'cho', 'từ', 'đến',
        'trong', 'ngoài', 'trên', 'dưới', 'bên', 'phía', 'cạnh', 'được',
        'bị', 'có', 'không', 'chưa', 'đã', 'sẽ', 'đang', 'vừa', 'này',
        'kia', 'nó', 'tôi', 'bạn', 'anh', 'chị', 'em', 'ông', 'bà',
    }
    
    def __init__(self):
        """Khởi tạo TextProcessor"""
        self.logger = logger
    
    def clean_text(self, text: str) -> str:
        """
        Làm sạch văn bản
        
        Args:
            text: Văn bản cần làm sạch
            
        Returns:
            Văn bản đã làm sạch
        """
        if not text:
            return ""
        
        # Loại bỏ các ký tự đặc biệt không cần thiết
        text = re.sub(self.SPECIAL_CHARS_PATTERN, '', text)
        
        # Chuẩn hóa khoảng trắng
        text = re.sub(self.WHITESPACE_PATTERN, ' ', text)
        
        # Loại bỏ khoảng trắng ở đầu và cuối
        text = text.strip()
        
        return text
    
    def normalize_vietnamese(self, text: str) -> str:
        """
        Chuẩn hóa văn bản tiếng Việt
        
        Args:
            text: Văn bản tiếng Việt
            
        Returns:
            Văn bản đã chuẩn hóa
        """
        if not text:
            return ""
        
        # Chuẩn hóa Unicode (NFD -> NFC)
        text = unicodedata.normalize('NFC', text)
        
        # Chuyển thành chữ thường
        text = text.lower()
        
        # Loại bỏ các ký tự diacritics nếu cần
        # (Tùy chọn - có thể bỏ qua để giữ diacritics)
        
        return text
    
    def remove_extra_whitespace(self, text: str) -> str:
        """
        Loại bỏ khoảng trắng thừa
        
        Args:
            text: Văn bản
            
        Returns:
            Văn bản đã xóa khoảng trắng thừa
        """
        # Xóa khoảng trắng ở đầu/cuối
        text = text.strip()
        
        # Xóa khoảng trắng thừa giữa các từ
        text = re.sub(r'\s+', ' ', text)
        
        # Xóa khoảng trắng trước dấu câu
        text = re.sub(r'\s+([.,!?;:])', r'\1', text)
        
        return text
    
    def remove_urls(self, text: str) -> str:
        """
        Loại bỏ URLs từ văn bản
        
        Args:
            text: Văn bản
            
        Returns:
            Văn bản đã xóa URLs
        """
        url_pattern = r'https?://\S+|www\.\S+'
        return re.sub(url_pattern, '', text)
    
    def remove_emails(self, text: str) -> str:
        """
        Loại bỏ email từ văn bản
        
        Args:
            text: Văn bản
            
        Returns:
            Văn bản đã xóa emails
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.sub(email_pattern, '', text)
    
    def remove_numbers(self, text: str, keep_decimals: bool = True) -> str:
        """
        Loại bỏ số từ văn bản
        
        Args:
            text: Văn bản
            keep_decimals: Giữ lại số thập phân
            
        Returns:
            Văn bản đã xóa số
        """
        if keep_decimals:
            # Giữ lại số thập phân (ví dụ: 3.14)
            pattern = r'\b\d+\b'
        else:
            # Xóa tất cả số
            pattern = r'\d+'
        
        return re.sub(pattern, '', text)
    
    def remove_stopwords(self, text: str, stopwords: Optional[set] = None) -> str:
        """
        Loại bỏ từ dừng (stopwords)
        
        Args:
            text: Văn bản
            stopwords: Tập hợp các từ dừng (mặc định là tiếng Việt)
            
        Returns:
            Văn bản đã xóa stopwords
        """
        if stopwords is None:
            stopwords = self.VIETNAMESE_STOPWORDS
        
        words = text.split()
        filtered_words = [w for w in words if w.lower() not in stopwords]
        return ' '.join(filtered_words)
    
    def remove_html_tags(self, text: str) -> str:
        """
        Loại bỏ HTML tags từ văn bản
        
        Args:
            text: Văn bản có HTML tags
            
        Returns:
            Văn bản đã xóa HTML tags
        """
        html_pattern = r'<[^>]+>'
        return re.sub(html_pattern, '', text)
    
    def remove_punctuation(self, text: str, keep_essential: bool = True) -> str:
        """
        Loại bỏ dấu câu
        
        Args:
            text: Văn bản
            keep_essential: Giữ lại dấu câu quan trọng (. , ! ?)
            
        Returns:
            Văn bản đã xóa dấu câu
        """
        if keep_essential:
            # Giữ lại dấu câu quan trọng
            pattern = r'[^\w\s\u0100-\u01B0\u1E00-\u1EFF\.\,\!\?]'
        else:
            # Xóa tất cả dấu câu
            pattern = r'[^\w\s\u0100-\u01B0\u1E00-\u1EFF]'
        
        return re.sub(pattern, '', text)
    
    def split_into_sentences(self, text: str) -> List[str]:
        """
        Chia văn bản thành các câu
        
        Args:
            text: Văn bản
            
        Returns:
            Danh sách các câu
        """
        # Chia theo dấu câu
        sentences = re.split(r'[.!?]+', text)
        
        # Loại bỏ câu trống và chuẩn hóa
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Chia văn bản thành các đoạn
        
        Args:
            text: Văn bản
            
        Returns:
            Danh sách các đoạn
        """
        # Chia theo dòng trống
        paragraphs = re.split(r'\n\n+', text)
        
        # Loại bỏ đoạn trống
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        return paragraphs
    
    def extract_keywords(self, text: str, num_keywords: int = 10) -> List[str]:
        """
        Trích xuất từ khóa từ văn bản
        
        Args:
            text: Văn bản
            num_keywords: Số lượng từ khóa cần trích xuất
            
        Returns:
            Danh sách từ khóa
        """
        # Chia thành từ
        words = text.split()
        
        # Loại bỏ stopwords
        words = [w for w in words if w.lower() not in self.VIETNAMESE_STOPWORDS]
        
        # Đếm tần suất từ
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Sắp xếp theo tần suất
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Lấy top N từ khóa
        keywords = [word for word, freq in sorted_words[:num_keywords]]
        
        return keywords
    
    def process_document(self, text: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Xử lý toàn bộ tài liệu với các bước chuẩn
        
        Args:
            text: Văn bản gốc
            config: Cấu hình xử lý (tùy chọn)
            
        Returns:
            Văn bản đã xử lý
        """
        if config is None:
            config = {
                'remove_urls': True,
                'remove_emails': True,
                'remove_html_tags': True,
                'normalize_vietnamese': True,
                'remove_extra_whitespace': True,
                'remove_numbers': False,
                'remove_stopwords': False,
            }
        
        # Áp dụng các bước xử lý
        if config.get('remove_html_tags', False):
            text = self.remove_html_tags(text)
        
        if config.get('remove_urls', False):
            text = self.remove_urls(text)
        
        if config.get('remove_emails', False):
            text = self.remove_emails(text)
        
        if config.get('normalize_vietnamese', False):
            text = self.normalize_vietnamese(text)
        
        if config.get('remove_numbers', False):
            text = self.remove_numbers(text)
        
        if config.get('remove_extra_whitespace', False):
            text = self.remove_extra_whitespace(text)
        
        if config.get('remove_stopwords', False):
            text = self.remove_stopwords(text)
        
        return text
    
    def get_text_statistics(self, text: str) -> Dict[str, Any]:
        """
        Lấy thống kê về văn bản
        
        Args:
            text: Văn bản
            
        Returns:
            Dictionary với thống kê
        """
        words = text.split()
        sentences = self.split_into_sentences(text)
        paragraphs = self.split_into_paragraphs(text)
        
        return {
            'character_count': len(text),
            'word_count': len(words),
            'sentence_count': len(sentences),
            'paragraph_count': len(paragraphs),
            'average_word_length': sum(len(w) for w in words) / len(words) if words else 0,
            'average_sentence_length': len(words) / len(sentences) if sentences else 0,
        }


class DocumentProcessor:
    """Xử lý toàn bộ tài liệu"""
    
    def __init__(self):
        """Khởi tạo DocumentProcessor"""
        self.text_processor = TextProcessor()
        self.logger = logger
    
    def process_documents(self, documents: List[Any], config: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Xử lý danh sách tài liệu
        
        Args:
            documents: Danh sách Document objects
            config: Cấu hình xử lý
            
        Returns:
            Danh sách tài liệu đã xử lý
        """
        processed_documents = []
        
        for doc in documents:
            try:
                # Xử lý nội dung
                processed_content = self.text_processor.process_document(doc.content, config)
                
                # Cập nhật metadata
                doc.metadata['processed'] = True
                doc.metadata['original_char_count'] = len(doc.content)
                doc.metadata['processed_char_count'] = len(processed_content)
                
                # Cập nhật nội dung
                doc.content = processed_content
                
                processed_documents.append(doc)
                self.logger.info(f"✅ Đã xử lý: {doc.filename}")
                
            except Exception as e:
                self.logger.error(f"❌ Lỗi xử lý {doc.filename}: {str(e)}")
        
        return processed_documents
