import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/api/generate")
    LLM_MODEL = os.getenv("LLM_MODEL_NAME", "business-qwen")
    COLLECTION_NAME = "enterprise_knowledge"

settings = Settings()