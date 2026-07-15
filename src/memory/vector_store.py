from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, SparseVectorParams, SparseVector
from FlagEmbedding import BGEM3FlagModel
from src.core.config import settings

class VectorStore:
    def __init__(self):
        self.client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.embedder = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
        self.collection = settings.COLLECTION_NAME
        self._init_collection()

    def _init_collection(self):
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config={"dense": VectorParams(size=1024, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams()}
            )

    def ingest(self, chunks: list):
        points = []
        for chunk in chunks:
            embeds = self.embedder.encode([chunk["text"]], return_dense=True, return_sparse=True)
            
            # 1. Trích xuất Dense Vector
            dense_vec = embeds['dense_vecs'][0].tolist()
            
            # 2. Xử lý Sparse Vector chuẩn theo yêu cầu của Qdrant
            lexical_weights = embeds['lexical_weights'][0]
            
            # Ép kiểu các key (từ vựng) sang số nguyên (int), và value (trọng số) sang float
            indices = [int(k) for k in lexical_weights.keys()]
            values = [float(v) for v in lexical_weights.values()]
            
            sparse_vec = SparseVector(indices=indices, values=values)

            # 3. Tạo PointStruct
            points.append(PointStruct(
                id=chunk["id"],
                vector={
                    "dense": dense_vec,
                    "sparse": sparse_vec
                },
                payload={"text": chunk["text"]}
            ))
            
            if len(points) >= 50:
                self.client.upsert(collection_name=self.collection, points=points)
                points = []
                
        if points: 
            self.client.upsert(collection_name=self.collection, points=points)