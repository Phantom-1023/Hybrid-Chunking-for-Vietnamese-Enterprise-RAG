"""Hybrid lexical/dense retrieval with an isolated, cache-backed index.

The web application passes this service only chunks that have already passed
its ACL query. The service deliberately knows nothing about Supabase or the
database, which keeps the experiment local and easy to test.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

import numpy as np

from src.bm25_retriever import BM25Result, BM25Retriever, LexicalDocument
from src.dense_retriever import DensePassageIndex
from src.local_embedding import LocalE5EmbeddingModel


@dataclass(frozen=True)
class RankedCandidate:
    candidate_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


@dataclass(frozen=True)
class FusedCandidate:
    candidate: RankedCandidate
    rrf_score: float
    rank: int
    source_ranks: Dict[str, int]


@dataclass(frozen=True)
class HybridResult:
    """A final hybrid result ready for citation construction."""

    document: LexicalDocument
    score: float
    method: str
    rrf_score: float | None = None
    source_ranks: Dict[str, int] = field(default_factory=dict)


class HybridRetrievalError(RuntimeError):
    """Raised when the local hybrid index cannot produce a result."""


def reciprocal_rank_fusion(
    rankings: Mapping[str, Iterable[RankedCandidate]],
    *,
    top_k: int = 20,
    rank_constant: int = 60,
) -> List[FusedCandidate]:
    """Fuse independent rankings without comparing their raw score scales."""
    if top_k <= 0:
        return []
    if rank_constant < 0:
        raise ValueError("rank_constant must be non-negative")

    candidates: Dict[str, RankedCandidate] = {}
    scores: Dict[str, float] = {}
    source_ranks: Dict[str, Dict[str, int]] = {}

    for source, ranking in rankings.items():
        seen_in_source: set[str] = set()
        for rank, candidate in enumerate(ranking, start=1):
            if candidate.candidate_id in seen_in_source:
                continue
            seen_in_source.add(candidate.candidate_id)
            candidates.setdefault(candidate.candidate_id, candidate)
            scores[candidate.candidate_id] = scores.get(candidate.candidate_id, 0.0) + (
                1.0 / (rank_constant + rank)
            )
            source_ranks.setdefault(candidate.candidate_id, {})[source] = rank

    ordered_ids = sorted(scores, key=lambda candidate_id: (-scores[candidate_id], candidate_id))
    return [
        FusedCandidate(
            candidate=candidates[candidate_id],
            rrf_score=scores[candidate_id],
            rank=rank,
            source_ranks=source_ranks[candidate_id],
        )
        for rank, candidate_id in enumerate(ordered_ids[:top_k], start=1)
    ]


class HybridRetriever:
    """Run BM25 and dense retrieval over an already ACL-filtered corpus."""

    def __init__(
        self,
        *,
        embedding_model=None,
        reranker=None,
        cache_path: str | Path | None = None,
        candidate_k: int = 20,
        batch_size: int = 32,
        rank_constant: int = 60,
    ):
        if candidate_k <= 0:
            raise ValueError("candidate_k must be positive")
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if rank_constant < 0:
            raise ValueError("rank_constant must be non-negative")
        self.embedding_model = embedding_model or LocalE5EmbeddingModel(
            device=os.getenv("WEBAPP_HYBRID_EMBEDDING_DEVICE", "cpu")
        )
        self.reranker = reranker
        self.cache_path = Path(
            cache_path
            or os.getenv(
                "WEBAPP_HYBRID_CACHE_PATH",
                ".cache/retrieval/web_hybrid_embeddings.npz",
            )
        )
        self.candidate_k = int(candidate_k)
        self.batch_size = int(batch_size)
        self.rank_constant = int(rank_constant)

    @property
    def model_name(self) -> str:
        return str(getattr(self.embedding_model, "model_name", "unknown"))

    @staticmethod
    def _cache_key(document: LexicalDocument) -> str:
        digest = hashlib.sha256(document.content.encode("utf-8")).hexdigest()
        return f"{document.document_id}:{digest}"

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.is_file():
            return {}
        try:
            with np.load(self.cache_path, allow_pickle=False) as cached:
                if str(cached["model_name"].item()) != self.model_name:
                    return {}
                keys = [str(value) for value in cached["keys"].tolist()]
                embeddings = np.asarray(cached["embeddings"], dtype=np.float32)
            if embeddings.ndim != 2 or len(keys) != len(embeddings):
                return {}
            return {key: embeddings[index] for index, key in enumerate(keys)}
        except (OSError, KeyError, ValueError, TypeError):
            return {}

    def _save_cache(self, entries: dict[str, np.ndarray]) -> None:
        if not entries:
            return
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        keys = list(entries)
        embeddings = np.asarray([entries[key] for key in keys], dtype=np.float32)
        temporary = self.cache_path.with_name(self.cache_path.name + ".tmp.npz")
        np.savez_compressed(
            temporary,
            keys=np.asarray(keys),
            embeddings=embeddings,
            model_name=np.asarray(self.model_name),
        )
        temporary.replace(self.cache_path)

    def _encode_documents(self, documents: list[LexicalDocument]) -> np.ndarray:
        cached = self._load_cache()
        keys = [self._cache_key(document) for document in documents]
        missing_indexes = [index for index, key in enumerate(keys) if key not in cached]
        if missing_indexes:
            missing_embeddings = self.embedding_model.encode_passages(
                [documents[index].content for index in missing_indexes],
                batch_size=self.batch_size,
            )
            matrix = np.asarray(missing_embeddings, dtype=np.float32)
            if matrix.ndim != 2 or matrix.shape[0] != len(missing_indexes):
                raise HybridRetrievalError(
                    "Embedding provider returned an invalid passage matrix"
                )
            for row, index in enumerate(missing_indexes):
                cached[keys[index]] = matrix[row]
            self._save_cache(cached)
        try:
            matrix = np.asarray([cached[key] for key in keys], dtype=np.float32)
        except (KeyError, ValueError) as exc:
            raise HybridRetrievalError("Embedding cache is incomplete") from exc
        if matrix.ndim != 2:
            raise HybridRetrievalError("Embedding cache returned an invalid matrix")
        return matrix

    @staticmethod
    def _candidate_from_bm25(result: BM25Result) -> RankedCandidate:
        return RankedCandidate(
            candidate_id=result.document.document_id,
            content=result.document.content,
            metadata=result.document.metadata,
            score=result.score,
        )

    @staticmethod
    def _candidate_from_dense(result) -> RankedCandidate:
        return RankedCandidate(
            candidate_id=result.document.document_id,
            content=result.document.content,
            metadata=result.document.metadata,
            score=result.score,
        )

    @staticmethod
    def _document_from_candidate(candidate: RankedCandidate) -> LexicalDocument:
        return LexicalDocument(
            document_id=candidate.candidate_id,
            content=candidate.content,
            metadata=candidate.metadata,
        )

    def retrieve(
        self,
        question: str,
        documents: Iterable[LexicalDocument],
        *,
        top_k: int = 5,
        bm25_results: Iterable[BM25Result] | None = None,
    ) -> list[HybridResult]:
        documents = list(documents)
        if top_k <= 0 or not documents:
            return []
        candidate_k = min(self.candidate_k, len(documents))
        lexical_results = list(
            bm25_results
            or BM25Retriever(documents).retrieve(question, top_k=candidate_k)
        )[:candidate_k]
        passage_embeddings = self._encode_documents(documents)
        query_embeddings = self.embedding_model.encode_queries([question], batch_size=1)
        query_matrix = np.asarray(query_embeddings, dtype=np.float32)
        if query_matrix.ndim != 2 or query_matrix.shape[0] != 1:
            raise HybridRetrievalError(
                "Embedding provider returned an invalid query matrix"
            )
        dense_results = DensePassageIndex(documents, passage_embeddings).retrieve(
            query_matrix[0], top_k=candidate_k
        )
        fused = reciprocal_rank_fusion(
            {
                "bm25": [self._candidate_from_bm25(item) for item in lexical_results],
                "dense": [self._candidate_from_dense(item) for item in dense_results],
            },
            top_k=candidate_k,
            rank_constant=self.rank_constant,
        )
        if not fused:
            return []
        fused_by_id = {item.candidate.candidate_id: item for item in fused}
        if self.reranker is not None:
            reranked = self.reranker.rerank(
                question,
                [item.candidate for item in fused],
                top_k=top_k,
            )
            return [
                HybridResult(
                    document=self._document_from_candidate(item.item),
                    score=item.score,
                    method="hybrid_rrf_then_fine_tuned_cross_encoder",
                    rrf_score=fused_by_id[item.item.candidate_id].rrf_score,
                    source_ranks=fused_by_id[item.item.candidate_id].source_ranks,
                )
                for item in reranked
            ]
        return [
            HybridResult(
                document=self._document_from_candidate(item.candidate),
                score=item.rrf_score,
                method="hybrid_rrf",
                rrf_score=item.rrf_score,
                source_ranks=item.source_ranks,
            )
            for item in fused[:top_k]
        ]
