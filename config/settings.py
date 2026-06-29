"""
Configuration settings for RAG Enterprise System
Supports environment variables and .env file loading
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Info
    app_name: str = os.getenv("APP_NAME", "RAG Enterprise System")
    app_env: str = os.getenv("APP_ENV", "development")
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Qdrant Configuration
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_api_key: str = os.getenv("QDRANT_API_KEY", "")
    
    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # LLM Configuration
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek").lower()
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    llm_model_name: str = os.getenv("LLM_MODEL_NAME", "qwen2.5:7b-instruct")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    deepseek_api_key: str = os.getenv("DEEPSEEK_API_KEY", "")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")

    # Gemini Configuration for current mission
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "text-embedding-004")
    gemini_flash_model: str = os.getenv("GEMINI_FLASH_MODEL", "gemini-1.5-flash")
    embedding_provider: str = os.getenv("EMBEDDING_PROVIDER", "gemini").lower()
    
    # Embedding Configuration
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
    embedding_device: str = os.getenv("EMBEDDING_DEVICE", "cpu")
    use_openai_embedding: bool = os.getenv("USE_OPENAI_EMBEDDING", "false").lower() == "true"
    
    # Data Processing
    chunk_size: int = int(os.getenv("CHUNK_SIZE", "500"))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", "50"))
    parent_chunk_size: int = int(os.getenv("PARENT_CHUNK_SIZE", "2200"))
    parent_chunk_overlap: int = int(os.getenv("PARENT_CHUNK_OVERLAP", "200"))
    child_chunk_size: int = int(os.getenv("CHILD_CHUNK_SIZE", "500"))
    child_chunk_overlap: int = int(os.getenv("CHILD_CHUNK_OVERLAP", "80"))
    top_k_retrieval: int = int(os.getenv("TOP_K_RETRIEVAL", "5"))
    similarity_threshold: float = float(os.getenv("SIMILARITY_THRESHOLD", "0.15"))

    # Mission dataset verification
    verify_dataset_name: str = os.getenv("VERIFY_DATASET_NAME", "sailor2/Vietnamese_RAG")
    verify_dataset_config: str = os.getenv("VERIFY_DATASET_CONFIG", "BKAI_RAG")
    verify_record_limit: int = int(os.getenv("VERIFY_RECORD_LIMIT", "50"))
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db/")
    index_embedding_batch_size: int = int(os.getenv("INDEX_EMBEDDING_BATCH_SIZE", "10"))
    index_batch_sleep_seconds: float = float(os.getenv("INDEX_BATCH_SLEEP_SECONDS", "1.0"))
    index_max_chunks_per_strategy: int = int(os.getenv("INDEX_MAX_CHUNKS_PER_STRATEGY", "0"))
    eval_limit: int = int(os.getenv("EVAL_LIMIT", "5"))
    eval_use_llm_generation: bool = os.getenv("EVAL_USE_LLM_GENERATION", "false").lower() == "true"
    
    # Data Paths
    data_storage_path: str = os.getenv("DATA_STORAGE_PATH", "./data")
    raw_data_path: str = os.path.join(data_storage_path, "raw")
    processed_data_path: str = os.path.join(data_storage_path, "processed")
    
    # Security
    enable_data_encryption: bool = os.getenv("ENABLE_DATA_ENCRYPTION", "true").lower() == "true"
    comply_with_vietnam_law: bool = os.getenv("COMPLY_WITH_VIETNAM_LAW", "true").lower() == "true"
    
    # Vietnamese NLP
    use_vietnamese_segmentation: bool = os.getenv("USE_VIETNAMESE_SEGMENTATION", "true").lower() == "true"
    underthesea_model_path: str = os.getenv("UNDERTHESEA_MODEL_PATH", "./models/underthesea")
    
    # API Configuration
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_workers: int = int(os.getenv("API_WORKERS", "4"))
    
    # Streamlit Configuration
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))
    streamlit_theme: str = os.getenv("STREAMLIT_THEME", "light")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

# Create global settings instance
settings = Settings()

# Ensure data directories exist
Path(settings.raw_data_path).mkdir(parents=True, exist_ok=True)
Path(settings.processed_data_path).mkdir(parents=True, exist_ok=True)
