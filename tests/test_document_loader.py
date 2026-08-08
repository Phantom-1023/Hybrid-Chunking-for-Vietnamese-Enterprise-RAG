"""
Test cases cho Document Loader Module
"""

import pytest
from pathlib import Path
from src.document_loader import DocumentLoader, DocumentManager, Document
from src.text_processor import TextProcessor


@pytest.fixture
def sample_documents(tmp_path: Path) -> Path:
    """Self-contained fixtures; tests must not depend on untracked demo data."""
    directory = tmp_path / "sample_documents"
    directory.mkdir()
    (directory / "sample_policy.txt").write_text(
        "Nhan vien duoc nghi phep theo chinh sach noi bo.", encoding="utf-8"
    )
    (directory / "handbook.md").write_text("# Handbook\nQuy trinh onboarding.", encoding="utf-8")
    return directory


class TestDocumentLoader:
    """Test DocumentLoader class"""
    
    @pytest.fixture
    def loader(self):
        """Tạo DocumentLoader instance"""
        return DocumentLoader()
    
    @pytest.fixture
    def text_processor(self):
        """Tạo TextProcessor instance"""
        return TextProcessor()
    
    def test_load_text_file(self, loader, sample_documents):
        """Test tải file text"""
        file_path = sample_documents / "sample_policy.txt"
        doc = loader.load_document(file_path)
        
        assert doc is not None
        assert doc.filename == "sample_policy.txt"
        assert len(doc.content) > 0
        assert doc.file_type == "Plain Text File"
    
    def test_load_nonexistent_file(self, loader):
        """Test tải file không tồn tại"""
        file_path = "data/sample_documents/nonexistent.txt"
        doc = loader.load_document(file_path)
        
        assert doc is None
    
    def test_load_unsupported_format(self, loader, sample_documents):
        """Test tải định dạng không được hỗ trợ"""
        # Tạo file với định dạng không hỗ trợ
        test_file = sample_documents / "test.xyz"
        test_file.write_text("test content")
        
        doc = loader.load_document(str(test_file))
        assert doc is None
        
        # Dọn dẹp
        test_file.unlink()
    
    def test_document_metadata(self, loader, sample_documents):
        """Test metadata của Document"""
        file_path = sample_documents / "sample_policy.txt"
        doc = loader.load_document(file_path)
        
        assert doc is not None
        assert doc.metadata['extension'] == '.txt'
        assert doc.metadata['file_size_bytes'] > 0
        assert doc.metadata['character_count'] > 0
        assert doc.metadata['word_count'] > 0
    
    def test_load_all_documents(self, loader, sample_documents):
        """Test tải tất cả tài liệu từ thư mục"""
        docs = loader.load_all_documents(sample_documents)
        
        assert len(docs) > 0
        assert all(isinstance(doc, Document) for doc in docs)


class TestTextProcessor:
    """Test TextProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Tạo TextProcessor instance"""
        return TextProcessor()
    
    def test_clean_text(self, processor):
        """Test làm sạch văn bản"""
        text = "Xin  chào!!!  Đây là   văn bản   test."
        cleaned = processor.clean_text(text)
        
        assert "  " not in cleaned
        assert cleaned.startswith("Xin")
    
    def test_normalize_vietnamese(self, processor):
        """Test chuẩn hóa tiếng Việt"""
        text = "XANH XANH"
        normalized = processor.normalize_vietnamese(text)
        
        assert normalized == "xanh xanh"
    
    def test_remove_urls(self, processor):
        """Test loại bỏ URLs"""
        text = "Truy cập https://example.com hoặc www.google.com"
        result = processor.remove_urls(text)
        
        assert "https://" not in result
        assert "www." not in result
    
    def test_remove_emails(self, processor):
        """Test loại bỏ emails"""
        text = "Email: test@example.com hoặc admin@company.vn"
        result = processor.remove_emails(text)
        
        assert "@" not in result
    
    def test_split_into_sentences(self, processor):
        """Test chia thành câu"""
        text = "Đây là câu 1. Đây là câu 2! Đây là câu 3?"
        sentences = processor.split_into_sentences(text)
        
        assert len(sentences) == 3
        assert all(s.strip() for s in sentences)
    
    def test_extract_keywords(self, processor):
        """Test trích xuất từ khóa"""
        text = "công ty công ty nhân viên nhân viên lương lương"
        keywords = processor.extract_keywords(text, num_keywords=3)
        
        assert len(keywords) <= 3
        assert all(isinstance(k, str) for k in keywords)
    
    def test_get_text_statistics(self, processor):
        """Test lấy thống kê văn bản"""
        text = "Đây là một câu. Đây là câu thứ hai."
        stats = processor.get_text_statistics(text)
        
        assert 'character_count' in stats
        assert 'word_count' in stats
        assert 'sentence_count' in stats
        assert stats['character_count'] > 0


class TestDocumentManager:
    """Test DocumentManager class"""
    
    @pytest.fixture
    def manager(self):
        """Tạo DocumentManager instance"""
        return DocumentManager()
    
    def test_add_document(self, manager, sample_documents):
        """Test thêm một tài liệu"""
        file_path = sample_documents / "sample_policy.txt"
        result = manager.add_document(file_path)
        
        assert result is True
        assert len(manager.get_all_documents()) > 0
    
    def test_add_documents_from_directory(self, manager, sample_documents):
        """Test thêm tài liệu từ thư mục"""
        count = manager.add_documents_from_directory(sample_documents)
        
        assert count > 0
        assert len(manager.get_all_documents()) == count
    
    def test_get_document_by_filename(self, manager, sample_documents):
        """Test tìm tài liệu theo tên"""
        manager.add_documents_from_directory(sample_documents)
        doc = manager.get_document_by_filename("sample_policy.txt")
        
        assert doc is not None
        assert doc.filename == "sample_policy.txt"
    
    def test_get_statistics(self, manager, sample_documents):
        """Test lấy thống kê"""
        manager.add_documents_from_directory(sample_documents)
        stats = manager.get_statistics()
        
        assert 'total_documents' in stats
        assert 'total_size_bytes' in stats
        assert 'total_characters' in stats
        assert 'total_words' in stats
        assert 'file_types' in stats
    
    def test_clear_documents(self, manager, sample_documents):
        """Test xóa tất cả tài liệu"""
        manager.add_documents_from_directory(sample_documents)
        assert len(manager.get_all_documents()) > 0
        
        manager.clear_documents()
        assert len(manager.get_all_documents()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
