from flashrank import Ranker, RerankRequest
from src.memory.vector_store import VectorStore

class HybridRetriever:
    def __init__(self):
        self.db = VectorStore()
        self.ranker = Ranker(model_name="ms-marco-MultiBERT-L-12")

    def search(self, query: str, top_k: int = 3) -> list:
        # Embed query
        query_embeds = self.db.embedder.encode([query], return_dense=True)
        dense_vec = query_embeds['dense_vecs'][0].tolist()

        # Hybrid Search
        results = self.db.client.query_points(
            collection_name=self.db.collection,
            query=dense_vec,       
            using="dense",         
            limit=top_k * 3
        ).points

        if not results: return []

        # Rerank
        passages = [{"id": hit.id, "text": hit.payload["text"]} for hit in results]
        reranked = self.ranker.rerank(RerankRequest(query=query, passages=passages))
        
        return [item["text"] for item in reranked[:top_k]]