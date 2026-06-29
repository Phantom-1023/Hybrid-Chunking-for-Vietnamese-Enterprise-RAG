"""
Constants for RAG Enterprise System
"""

# Supported Document Formats
SUPPORTED_DOCUMENT_FORMATS = {
    ".pdf": "PDF Document",
    ".docx": "Microsoft Word Document",
    ".doc": "Microsoft Word Document (Legacy)",
    ".txt": "Plain Text File",
    ".md": "Markdown File",
    ".csv": "CSV Spreadsheet",
    ".xlsx": "Excel Workbook",
    ".xls": "Excel Workbook (Legacy)",
}

# Vietnamese Language Constants
VIETNAMESE_STOPWORDS = {
    "và", "hoặc", "nhưng", "tuy", "vì", "do", "nếu", "thì", "khi", "mà",
    "là", "cái", "chiếc", "những", "cái", "những", "các", "của", "cho",
    "từ", "đến", "trong", "ngoài", "trên", "dưới", "bên", "phía", "cạnh",
    "được", "bị", "có", "không", "chưa", "đã", "sẽ", "đang", "vừa",
    "này", "kia", "nó", "nó", "tôi", "bạn", "anh", "chị", "em",
}

# Chunking Strategy
DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 50
VERIFY_DATASET_NAME = "sailor2/Vietnamese_RAG"
VERIFY_DATASET_CONFIG = "BKAI_RAG"
VERIFY_RECORD_LIMIT = 50
VERIFY_STRATEGIES = ("fixed", "recursive", "semantic", "paragraph")
GEMINI_EMBEDDING_MODEL = "text-embedding-004"
CHROMA_DB_PATH = "./chroma_db/"
INDEX_EMBEDDING_BATCH_SIZE = 10
INDEX_BATCH_SLEEP_SECONDS = 1.0
STRATEGY_COLLECTIONS = {
    "fixed": "collection_fixed",
    "recursive": "collection_recursive",
    "semantic": "collection_semantic",
    "paragraph": "collection_paragraph",
}
DEFAULT_PARENT_CHUNK_SIZE = 2200
DEFAULT_PARENT_CHUNK_OVERLAP = 200
DEFAULT_CHILD_CHUNK_SIZE = 500
DEFAULT_CHILD_CHUNK_OVERLAP = 80
MIN_CHUNK_SIZE = 100
MAX_CHUNK_SIZE = 2000

# Retrieval Configuration
DEFAULT_TOP_K = 5
MIN_TOP_K = 1
MAX_TOP_K = 20
SIMILARITY_THRESHOLD = 0.3

# Reranking Configuration
RERANKER_MODEL = "BAAI/bge-reranker-v2-m3"
RERANKER_BATCH_SIZE = 32

# Embedding Configuration
DEFAULT_EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_DIMENSION = 384  # For BGE-M3
EMBEDDING_BATCH_SIZE = 32

# LLM Configuration
DEFAULT_LLM_TEMPERATURE = 0.7
DEFAULT_LLM_MAX_TOKENS = 1024
DEFAULT_LLM_TOP_P = 0.9

# Qdrant Configuration
QDRANT_COLLECTION_NAME = "vietnamese_documents"
QDRANT_VECTOR_SIZE = 384  # Must match embedding dimension
QDRANT_DISTANCE_METRIC = "Cosine"

# Redis Configuration
REDIS_CACHE_TTL = 3600  # 1 hour
REDIS_PREFIX = "rag:"

# API Response Codes
SUCCESS_CODE = 200
ERROR_CODE = 500
NOT_FOUND_CODE = 404
VALIDATION_ERROR_CODE = 422

# Logging Configuration
LOG_FORMAT = "[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Error Messages
ERROR_MESSAGES = {
    "document_not_found": "Tài liệu không được tìm thấy.",
    "invalid_format": "Định dạng tài liệu không được hỗ trợ.",
    "embedding_failed": "Không thể tạo embedding cho tài liệu.",
    "retrieval_failed": "Không thể truy xuất dữ liệu từ vector database.",
    "llm_error": "Lỗi khi gọi LLM.",
    "database_connection_error": "Lỗi kết nối cơ sở dữ liệu.",
}

# Success Messages
SUCCESS_MESSAGES = {
    "document_uploaded": "Tài liệu đã được tải lên thành công.",
    "document_processed": "Tài liệu đã được xử lý thành công.",
    "query_processed": "Truy vấn đã được xử lý thành công.",
}

# Vietnamese Language Specific
VIETNAMESE_LANGUAGE_CODE = "vi"
VIETNAMESE_ENCODING = "utf-8"

# Data Compliance
COMPLY_WITH_VIETNAM_CYBERSECURITY_LAW = True
DATA_STORAGE_LOCATION = "Vietnam"  # Must be in Vietnam per law
ENCRYPTION_ALGORITHM = "AES-256"
