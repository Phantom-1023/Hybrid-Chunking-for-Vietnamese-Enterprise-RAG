"""
Dataset loader for the current chunking benchmark mission.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import re

from config.constants import VERIFY_DATASET_CONFIG, VERIFY_DATASET_NAME, VERIFY_RECORD_LIMIT


class DatasetLoadError(RuntimeError):
    """Raised when the HuggingFace dataset cannot be loaded."""


@dataclass
class RagDatasetRecord:
    """Normalized dataset row used by verify/index/evaluation steps."""

    record_id: str
    question: Optional[str]
    ground_truth: Optional[str]
    joined_context: str
    raw: Dict[str, Any]


@dataclass
class RagDatasetSnapshot:
    """Small normalized dataset snapshot for mission verification."""

    dataset_name: str
    config_name: str
    total_records: int
    selected_records: List[RagDatasetRecord]
    schema_fields: List[str]


def load_vietnamese_rag_snapshot(
    dataset_name: str = VERIFY_DATASET_NAME,
    config_name: str = VERIFY_DATASET_CONFIG,
    limit: int = VERIFY_RECORD_LIMIT,
) -> RagDatasetSnapshot:
    """Load and normalize up to `limit` records from the mission dataset."""
    try:
        from datasets import load_dataset
    except ImportError as exc:
        raise DatasetLoadError(
            "Missing datasets package. Please install dependencies from requirements.txt."
        ) from exc

    try:
        dataset = load_dataset(dataset_name, config_name, split="train")
    except Exception as exc:
        raise DatasetLoadError(
            f"Could not load dataset '{dataset_name}' with config '{config_name}'. "
            "Please check internet access and the datasets package."
        ) from exc

    total_records = len(dataset)
    selected_count = min(limit, total_records)
    schema_fields = list(getattr(dataset, "column_names", []) or [])
    selected_records: List[RagDatasetRecord] = []

    for index in range(selected_count):
        row = dict(dataset[index])
        selected_records.append(_normalize_record(row, index))

    return RagDatasetSnapshot(
        dataset_name=dataset_name,
        config_name=config_name,
        total_records=total_records,
        selected_records=selected_records,
        schema_fields=schema_fields,
    )


def _normalize_record(row: Dict[str, Any], index: int) -> RagDatasetRecord:
    question = _string_or_none(row.get("question"))
    ground_truth = _first_present_string(row, ["ground_truth", "ground_truths", "answer", "answers"])
    context_value = _first_present_value(row, ["context", "contexts", "passages", "documents"])

    return RagDatasetRecord(
        record_id=str(row.get("id") or row.get("_id") or index),
        question=question,
        ground_truth=ground_truth,
        joined_context=join_context(context_value),
        raw=row,
    )


def join_context(context_value: Any) -> str:
    """Join dataset context/passages into one clean text string."""
    if context_value is None:
        return ""

    if isinstance(context_value, str):
        parts = [context_value]
    elif isinstance(context_value, (list, tuple)):
        parts = [_context_part_to_text(item) for item in context_value]
    else:
        parts = [_context_part_to_text(context_value)]

    joined = "\n\n".join(part.strip() for part in parts if part and part.strip())
    return re.sub(r"[ \t]+", " ", joined).strip()


def _context_part_to_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        for key in ("text", "content", "passage", "context"):
            if key in value and value[key]:
                return str(value[key])
        return " ".join(str(item) for item in value.values() if item)
    return str(value)


def _first_present_value(row: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def _first_present_string(row: Dict[str, Any], keys: List[str]) -> Optional[str]:
    value = _first_present_value(row, keys)
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    return _string_or_none(value)


def _string_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
