"""
Indexing pipeline for C-004: 4 chunking strategies into ChromaDB.
"""

from dataclasses import dataclass
from time import sleep
from typing import Dict, List

from config.constants import STRATEGY_COLLECTIONS, VERIFY_STRATEGIES
from config.settings import settings
from src.ai_gateway import EmbeddingProvider, EmbeddingProviderError
from src.chroma_store import ChromaStoreError, ChromaVectorStore
from src.chunking import Chunk, chunk_text_by_strategy
from src.dataset_loader import DatasetLoadError, RagDatasetSnapshot, load_vietnamese_rag_snapshot
from src.gemini_service import MissingGeminiApiKey


class IndexingError(RuntimeError):
    """Raised when indexing cannot complete."""


@dataclass
class IndexingReport:
    """Summary printed by main.py after indexing."""

    dataset_name: str
    config_name: str
    total_records: int
    selected_records: int
    chroma_path: str
    chunk_counts: Dict[str, int]
    indexed_chunk_counts: Dict[str, int]
    collection_counts: Dict[str, int]
    query_result_counts: Dict[str, int]
    semantic_fallback_used: bool


@dataclass
class IndexingInputs:
    """Prepared dataset and chunks before embedding/storage."""

    snapshot: RagDatasetSnapshot
    chunks_by_strategy: Dict[str, List[Chunk]]
    semantic_fallback_used: bool


def prepare_indexing_inputs() -> IndexingInputs:
    snapshot = _load_snapshot()
    chunks_by_strategy = _chunk_snapshot(snapshot)
    return IndexingInputs(
        snapshot=snapshot,
        chunks_by_strategy=chunks_by_strategy,
        semantic_fallback_used=_semantic_fallback_used(chunks_by_strategy.get("semantic", [])),
    )


def run_indexing_pipeline(prepared: IndexingInputs = None) -> IndexingReport:
    prepared = prepared or prepare_indexing_inputs()
    snapshot = prepared.snapshot
    chunks_by_strategy = prepared.chunks_by_strategy
    chunks_to_index = _limit_chunks_for_execution(chunks_by_strategy)

    provider = EmbeddingProvider()
    store = ChromaVectorStore(path=settings.chroma_db_path)

    for strategy in VERIFY_STRATEGIES:
        collection_name = STRATEGY_COLLECTIONS[strategy]
        store.reset_collection(collection_name)
        _embed_and_store_strategy(
            store=store,
            provider=provider,
            collection_name=collection_name,
            chunks=chunks_to_index[strategy],
            strategy=strategy,
        )

    collection_counts = {
        STRATEGY_COLLECTIONS[strategy]: store.count(STRATEGY_COLLECTIONS[strategy])
        for strategy in VERIFY_STRATEGIES
    }
    query_result_counts = _run_query_smoke_tests(snapshot, store, provider)

    return IndexingReport(
        dataset_name=snapshot.dataset_name,
        config_name=snapshot.config_name,
        total_records=snapshot.total_records,
        selected_records=len(snapshot.selected_records),
        chroma_path=settings.chroma_db_path,
        chunk_counts={strategy: len(chunks_by_strategy[strategy]) for strategy in VERIFY_STRATEGIES},
        indexed_chunk_counts={strategy: len(chunks_to_index[strategy]) for strategy in VERIFY_STRATEGIES},
        collection_counts=collection_counts,
        query_result_counts=query_result_counts,
        semantic_fallback_used=prepared.semantic_fallback_used,
    )


def _load_snapshot() -> RagDatasetSnapshot:
    try:
        return load_vietnamese_rag_snapshot(
            dataset_name=settings.verify_dataset_name,
            config_name=settings.verify_dataset_config,
            limit=settings.verify_record_limit,
        )
    except DatasetLoadError:
        raise


def _chunk_snapshot(snapshot: RagDatasetSnapshot) -> Dict[str, List[Chunk]]:
    chunks_by_strategy: Dict[str, List[Chunk]] = {strategy: [] for strategy in VERIFY_STRATEGIES}

    for record in snapshot.selected_records:
        if not record.joined_context:
            continue
        for strategy in VERIFY_STRATEGIES:
            chunks = chunk_text_by_strategy(
                strategy=strategy,
                text=record.joined_context,
                source_document=f"record_{record.record_id}",
                metadata={
                    "record_id": record.record_id,
                    "question": record.question or "",
                    "strategy": strategy,
                },
            )
            chunks_by_strategy[strategy].extend(chunks)

    for strategy, chunks in chunks_by_strategy.items():
        if not chunks:
            raise IndexingError(f"No chunks produced for strategy '{strategy}'.")

    return chunks_by_strategy


def _limit_chunks_for_execution(chunks_by_strategy: Dict[str, List[Chunk]]) -> Dict[str, List[Chunk]]:
    limit = settings.index_max_chunks_per_strategy
    if limit <= 0:
        return chunks_by_strategy
    return {
        strategy: chunks[:limit]
        for strategy, chunks in chunks_by_strategy.items()
    }


def _embed_and_store_strategy(
    store: ChromaVectorStore,
    provider: EmbeddingProvider,
    collection_name: str,
    chunks: List[Chunk],
    strategy: str,
) -> None:
    batch_size = max(1, settings.index_embedding_batch_size)
    sleep_seconds = max(0.0, settings.index_batch_sleep_seconds)

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start:start + batch_size]
        texts = [chunk.content for chunk in batch]
        embeddings = provider.embed_texts(texts)
        ids = [
            f"{strategy}_{chunk.source_document}_{chunk.chunk_index}_{start + offset}"
            for offset, chunk in enumerate(batch)
        ]
        metadatas = [
            {
                **(chunk.metadata or {}),
                "source_document": chunk.source_document,
                "chunk_index": chunk.chunk_index,
                "start_char": chunk.start_char,
                "end_char": chunk.end_char,
            }
            for chunk in batch
        ]
        store.add_embeddings(
            collection_name=collection_name,
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        if sleep_seconds and start + batch_size < len(chunks):
            sleep(sleep_seconds)


def _run_query_smoke_tests(
    snapshot: RagDatasetSnapshot,
    store: ChromaVectorStore,
    provider: EmbeddingProvider,
) -> Dict[str, int]:
    query_text = next(
        (record.question for record in snapshot.selected_records if record.question),
        "kiểm tra truy vấn",
    )
    query_embedding = provider.embed_text(query_text)
    result_counts: Dict[str, int] = {}

    for strategy in VERIFY_STRATEGIES:
        collection_name = STRATEGY_COLLECTIONS[strategy]
        results = store.query(
            collection_name=collection_name,
            query_embedding=query_embedding,
            top_k=5,
        )
        result_counts[collection_name] = len(results)

    return result_counts


def _semantic_fallback_used(chunks: List[Chunk]) -> bool:
    return any(chunk.metadata.get("semantic_fallback_used") for chunk in chunks)
