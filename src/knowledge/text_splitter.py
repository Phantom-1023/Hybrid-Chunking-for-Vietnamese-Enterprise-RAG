from underthesea import word_tokenize
from langchain_text_splitters import RecursiveCharacterTextSplitter

def process_vietnamese_text(text: str) -> str:
    """Tiền xử lý tiếng Việt bằng Underthesea"""
    if not text: return ""
    return word_tokenize(text, format="text")

def chunk_documents(texts: list) -> list:
    """Chia nhỏ văn bản"""
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    chunks = splitter.create_documents([t for t in texts if t])
    
    processed = []
    for i, chunk in enumerate(chunks):
        processed_text = process_vietnamese_text(chunk.page_content)
        if processed_text.strip():
            processed.append({"id": i, "text": processed_text})
    return processed