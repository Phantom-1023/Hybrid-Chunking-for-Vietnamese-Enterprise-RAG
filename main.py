"""
Main entry point for RAG Enterprise System
"""

import sys
import argparse
import logging
import os
import subprocess
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.chunking import chunk_text_by_strategy
from src.dataset_loader import DatasetLoadError, load_vietnamese_rag_snapshot
from src.gemini_service import GeminiEmbeddingError, GeminiService, MissingGeminiApiKey
from src.ai_gateway import EmbeddingProviderError
from src.chroma_store import ChromaStoreError
from src.evaluator_lite import EvaluationLiteError, run_evaluation_lite
from src.generator import AnswerGenerator
from src.indexer import IndexingError, prepare_indexing_inputs, run_indexing_pipeline
from src.retriever import RetrieverError, StrategyRetriever
from src.utils import setup_logger
from config.constants import VERIFY_STRATEGIES
from config.settings import settings

logger = setup_logger(__name__)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="RAG Enterprise System - Vietnamese Knowledge Management"
    )
    
    parser.add_argument(
        "--mode",
        choices=["streamlit", "api", "cli", "verify", "index", "query", "evaluate-lite"],
        default="streamlit",
        help="Run mode: streamlit (UI), api (FastAPI), cli, verify, index, query, or evaluate-lite"
    )
    parser.add_argument(
        "--strategy",
        choices=["fixed", "recursive", "semantic", "paragraph"],
        default="fixed",
        help="Chunking strategy to query in --mode query"
    )
    parser.add_argument(
        "--question",
        default="",
        help="Question to ask in --mode query"
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of source chunks to retrieve in --mode query/evaluate-lite"
    )
    parser.add_argument(
        "--eval-limit",
        type=int,
        default=settings.eval_limit,
        help="Number of dataset records for --mode evaluate-lite, clamped to 1-5"
    )
    
    args = parser.parse_args()
    
    if args.mode not in {"verify", "index", "query", "evaluate-lite"}:
        logger.info(f"Starting RAG Enterprise System in {args.mode} mode")
    
    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "api":
        run_api()
    elif args.mode == "cli":
        run_cli()
    elif args.mode == "verify":
        run_verify()
    elif args.mode == "index":
        run_index()
    elif args.mode == "query":
        run_query(args.strategy, args.question, args.top_k)
    elif args.mode == "evaluate-lite":
        run_evaluate_lite(args.eval_limit, args.top_k)


def run_streamlit():
    """Run Streamlit UI"""
    logger.info("Starting Streamlit UI...")
    try:
        # Sử dụng ui/app.py thay vì ui/streamlit_app.py
        subprocess.run([
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "ui/app.py",
            f"--server.port={settings.streamlit_port}",
            "--server.address=0.0.0.0"
        ])
    except KeyboardInterrupt:
        logger.info("Streamlit server stopped by user")
    except Exception as e:
        logger.error(f"Error running Streamlit: {e}")
        sys.exit(1)


def run_api():
    """Run FastAPI server - Placeholder"""
    logger.info("API mode not yet implemented")


def run_cli():
    """Run CLI interface - Placeholder"""
    logger.info("CLI mode not yet implemented")


def run_verify():
    """Verify Milestone 1 inputs: dataset, chunkers, and Gemini embedding."""
    logging.getLogger("src.chunking").setLevel(logging.ERROR)

    print("=== RAG ENTERPRISE VERIFY ===")
    print(f"Dataset name: {settings.verify_dataset_name}")
    print(f"Config: {settings.verify_dataset_config}")

    try:
        snapshot = load_vietnamese_rag_snapshot(
            dataset_name=settings.verify_dataset_name,
            config_name=settings.verify_dataset_config,
            limit=settings.verify_record_limit,
        )
    except DatasetLoadError as exc:
        print(f"Dataset load error: {exc}")
        if exc.__cause__:
            print(f"Underlying error: {repr(exc.__cause__)}")
        print("Suggestion: check internet access and the datasets package.")
        return

    selected_count = len(snapshot.selected_records)
    print(f"Total records loaded: {snapshot.total_records}")
    print(f"Records selected: {selected_count}")
    print(f"Schema fields: {', '.join(snapshot.schema_fields)}")

    sample = _select_sample_record(snapshot.selected_records)
    if not sample:
        print("Dataset load error: selected records do not contain non-empty context text.")
        return

    print(f"Sample question: {sample.question or 'N/A'}")
    print(f"Sample ground_truth: {sample.ground_truth or 'N/A'}")
    print("Sample joined context text:")
    print(_truncate(sample.joined_context, 700))

    print("\nChunk counts:")
    strategy_chunks = {}
    semantic_fallback_used = False
    for strategy in VERIFY_STRATEGIES:
        chunks = chunk_text_by_strategy(
            strategy=strategy,
            text=sample.joined_context,
            source_document=f"record_{sample.record_id}",
            metadata={"record_id": sample.record_id},
        )
        strategy_chunks[strategy] = chunks
        if strategy == "semantic":
            semantic_fallback_used = any(
                chunk.metadata.get("semantic_fallback_used") for chunk in chunks
            )
        print(f"{strategy}: {len(chunks)}")

    if semantic_fallback_used:
        print("Semantic fallback used")

    print("\nGemini embedding test:")
    try:
        embedding = GeminiService().embed_text(sample.joined_context[:1000])
        print("Success")
        print(f"Model: {embedding.model}")
        print(f"Vector dimension: {embedding.dimension}")
    except MissingGeminiApiKey as exc:
        print(str(exc))
    except GeminiEmbeddingError as exc:
        print(f"Gemini embedding error: {exc}")


def run_index():
    """Index 50 Vietnamese_RAG records into 4 local ChromaDB collections."""
    logging.getLogger("src.chunking").setLevel(logging.ERROR)

    print("=== RAG ENTERPRISE INDEX ===")
    print(f"Dataset name: {settings.verify_dataset_name}")
    print(f"Config: {settings.verify_dataset_config}")
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Embedding model: {settings.gemini_embedding_model}")
    if settings.gemini_embedding_model == "gemini-embedding-001":
        print(
            "Execution Patch: using gemini-embedding-001 because text-embedding-004 "
            "is not supported by current API key."
        )
    if settings.index_max_chunks_per_strategy > 0:
        print(
            f"Execution Patch: indexing first {settings.index_max_chunks_per_strategy} "
            "chunks per strategy to stay within current Gemini free-tier quota."
        )

    try:
        prepared = prepare_indexing_inputs()
        snapshot = prepared.snapshot
        print("Dataset loaded.")
        print(f"Total records loaded: {snapshot.total_records}")
        print(f"Records selected: {len(snapshot.selected_records)}")

        print("\nChunk count per strategy:")
        for strategy, chunks in prepared.chunks_by_strategy.items():
            print(f"{strategy}: {len(chunks)}")
        if prepared.semantic_fallback_used:
            print("Semantic fallback used")
        print(f"ChromaDB path: {settings.chroma_db_path}")

        report = run_indexing_pipeline(prepared)
    except MissingGeminiApiKey as exc:
        print(str(exc))
        return
    except DatasetLoadError as exc:
        print(f"Dataset load error: {exc}")
        if exc.__cause__:
            print(f"Underlying error: {repr(exc.__cause__)}")
        print("Suggestion: check internet access and the datasets package.")
        return
    except EmbeddingProviderError as exc:
        print(f"Embedding provider error: {exc}")
        return
    except ChromaStoreError as exc:
        print(f"ChromaDB error: {exc}")
        return
    except IndexingError as exc:
        print(f"Indexing error: {exc}")
        return

    print("\nCollection count:")
    for collection_name, count in report.collection_counts.items():
        print(f"{collection_name}: {count}")

    print("\nTest query result count:")
    for collection_name, count in report.query_result_counts.items():
        print(f"{collection_name}: {count}")


def run_query(strategy: str, question: str, top_k: int = 5):
    """Run a minimal live query against one ChromaDB strategy collection."""
    if not question.strip():
        print("Missing question. Please pass --question \"...\"")
        return

    print("=== RAG ENTERPRISE QUERY ===")
    print(f"Selected strategy: {strategy}")
    print(f"Question: {question}")
    print(f"Embedding provider: {settings.embedding_provider}")
    print(f"Embedding model: {settings.gemini_embedding_model}")
    if settings.gemini_embedding_model == "gemini-embedding-001":
        print(
            "Execution Patch: using gemini-embedding-001 because text-embedding-004 "
            "is not supported by current API key."
        )

    try:
        chunks = StrategyRetriever().retrieve(question=question, strategy=strategy, top_k=top_k)
    except (MissingGeminiApiKey, EmbeddingProviderError, ChromaStoreError, RetrieverError) as exc:
        print(f"Query error: {exc}")
        return

    answer = AnswerGenerator().generate(question, chunks)

    print("\nAnswer:")
    print(answer)

    print("\nTop source chunks:")
    for index, chunk in enumerate(chunks, start=1):
        print(f"\n[{index}] distance: {chunk.distance:.4f}")
        print(f"metadata: {chunk.metadata}")
        print(_truncate(chunk.content, 900))


def run_evaluate_lite(eval_limit: int = 5, top_k: int = 5):
    """Run a tiny real benchmark over existing ChromaDB collections."""
    print("=== RAG ENTERPRISE EVALUATION-LITE ===")
    print("This is evaluation-lite, not full RAGAS.")
    print("RAGAS status: not completed in this command.")
    print(f"Dataset name: {settings.verify_dataset_name}")
    print(f"Config: {settings.verify_dataset_config}")
    print(f"Requested EVAL_LIMIT: {eval_limit}")
    print("Effective sample limit: 1-5 records")
    print(f"Top-k: {top_k}")
    print(f"Embedding model: {settings.gemini_embedding_model}")
    print(f"LLM generation in evaluation: {'enabled' if settings.eval_use_llm_generation else 'skipped'}")
    if not settings.eval_use_llm_generation:
        print("answer_keyword_overlap uses retrieved source chunks, not a generated LLM answer.")
    if settings.gemini_embedding_model == "gemini-embedding-001":
        print(
            "Execution Patch: using gemini-embedding-001 because text-embedding-004 "
            "is not supported by current API key."
        )

    try:
        results = run_evaluation_lite(limit=eval_limit, top_k=top_k)
    except MissingGeminiApiKey as exc:
        print(str(exc))
        return
    except DatasetLoadError as exc:
        print(f"Dataset load error: {exc}")
        if exc.__cause__:
            print(f"Underlying error: {repr(exc.__cause__)}")
        print("Suggestion: check internet access and the datasets package.")
        return
    except (EmbeddingProviderError, ChromaStoreError, RetrieverError, EvaluationLiteError) as exc:
        print(f"Evaluation-lite error: {exc}")
        return

    print("\nMetrics:")
    print("strategy | sample_count | top1_hit_rate | topk_hit_rate | avg_distance | answer_keyword_overlap | avg_score")
    for result in results:
        print(
            f"{result.strategy} | {result.sample_count} | "
            f"{result.top1_hit_rate:.4f} | {result.topk_hit_rate:.4f} | "
            f"{result.avg_distance:.4f} | {result.answer_keyword_overlap:.4f} | "
            f"{result.avg_score:.4f}"
        )
    print("\nCSV written: benchmark_results.csv")
    print("Note: This is evaluation-lite, not full RAGAS.")


def _select_sample_record(records):
    for record in records:
        if record.joined_context:
            return record
    return records[0] if records else None


def _truncate(text: str, max_length: int) -> str:
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


if __name__ == "__main__":
    main()
