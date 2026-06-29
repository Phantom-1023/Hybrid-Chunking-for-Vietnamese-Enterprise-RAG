"""
Embedding Service Module
Tạo embedding vectors cho các chunks sử dụng OpenAI hoặc Local Models
"""

import os
import hashlib
from typing import List, Dict, Any, Optional, Union
import numpy as np
from src.utils import setup_logger, retry_on_exception
from config.settings import settings

logger = setup_logger(__name__)


class EmbeddingService:
    """Dịch vụ tạo embedding"""
    
    def __init__(self):
        """Khởi tạo EmbeddingService"""
        self.logger = logger
        self.use_openai = settings.use_openai_embedding
        self.model_name = settings.embedding_model
        self.device = settings.embedding_device
        
        self.client = None
        self.local_model = None
        self.fallback_dimension = 384
        
        if self.use_openai:
            self._init_openai()
        else:
            self._init_local_model()
    
    def _init_openai(self):
        """Khởi tạo OpenAI client"""
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.openai_api_key)
            self.logger.info(f"✅ OpenAI Embedding initialized with model: {self.model_name}")
        except ImportError:
            self.logger.error("openai library not installed. Run: pip install openai")
            self.use_openai = False
            self._init_local_model()
        except Exception as e:
            self.logger.error(f"Error initializing OpenAI: {e}")
            self.use_openai = False
            self._init_local_model()
    
    def _init_local_model(self):
        """Khởi tạo Local Sentence Transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            self.logger.info(f"Loading local embedding model: {self.model_name} on {self.device}...")
            self.local_model = SentenceTransformer(self.model_name, device=self.device)
            self.logger.info(f"✅ Local Embedding model loaded successfully")
        except ImportError:
            self.logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
        except Exception as e:
            self.logger.error(f"Error loading local model: {e}")
    
    @retry_on_exception(max_retries=3, delay=2)
    def embed_text(self, text: str) -> List[float]:
        """
        Tạo embedding cho một đoạn văn bản
        
        Args:
            text: Văn bản cần embed
            
        Returns:
            Vector embedding (list of floats)
        """
        if not text:
            return []
            
        if self.use_openai:
            response = self.client.embeddings.create(
                input=text,
                model=self.model_name
            )
            return response.data[0].embedding
        else:
            if self.local_model:
                embedding = self.local_model.encode(text)
                return embedding.tolist()
            else:
                self.logger.error("No embedding model available")
                return self._fallback_embed(text)
    
    def embed_chunks(self, chunks: List[Any]) -> List[List[float]]:
        """
        Tạo embedding cho danh sách các chunks
        
        Args:
            chunks: Danh sách Chunk hoặc SegmentedChunk objects
            
        Returns:
            Danh sách các vectors
        """
        texts = []
        for chunk in chunks:
            # Ưu tiên sử dụng segmented_content nếu có
            if hasattr(chunk, 'segmented_content'):
                texts.append(chunk.segmented_content)
            else:
                texts.append(chunk.content)
        
        if not texts:
            return []
            
        self.logger.info(f"Generating embeddings for {len(texts)} chunks...")
        
        if self.use_openai:
            # OpenAI supports batching
            embeddings = []
            # Batch size for OpenAI is typically 100-200
            batch_size = 100
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                response = self.client.embeddings.create(
                    input=batch,
                    model=self.model_name
                )
                embeddings.extend([item.embedding for item in response.data])
            return embeddings
        else:
            if self.local_model:
                # SentenceTransformers handles batching internally
                embeddings = self.local_model.encode(texts, show_progress_bar=True)
                return embeddings.tolist()
            else:
                self.logger.error("No embedding model available")
                return [self._fallback_embed(text) for text in texts]
    
    def get_embedding_dimension(self) -> int:
        """Lấy kích thước của vector embedding"""
        test_text = "test"
        vector = self.embed_text(test_text)
        return len(vector)

    def _fallback_embed(self, text: str) -> List[float]:
        """Deterministic hashing embedding for offline demos when model loading fails."""
        vector = np.zeros(self.fallback_dimension, dtype=float)
        tokens = [token for token in text.lower().split() if token]
        if not tokens:
            return vector.tolist()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % self.fallback_dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign

        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()
