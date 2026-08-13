"""Acceptance checks for deterministic long-document ingestion and retrieval.

The fixture is synthetic and is not part of the training or benchmark corpus.
It verifies the local text-ingestion and BM25 retrieval path only.  It does not
establish neural-model, generation, document-domain, or production performance.
"""

import pytest

from src.bm25_retriever import BM25Retriever, LexicalDocument
from webapp.ingestion import (
    MAX_UPLOAD_BYTES,
    IngestionError,
    extract_uploaded_document,
)


FACTS = {
    "beginning": "Mã kiểm soát đầu tài liệu là ALPHA-2719.",
    "middle": "Chu kỳ kiểm kê giữa tài liệu là 37 ngày.",
    "end": "Ngưỡng phê duyệt cuối tài liệu là 842 triệu đồng.",
}


def _long_unseen_document() -> str:
    filler = (
        "Quy trình nội bộ mô tả trách nhiệm, thời hạn xử lý và bằng chứng lưu vết. "
        "Nội dung nền này cố ý không chứa các mã hoặc con số dùng trong truy vấn. "
    )
    return "\n\n".join(
        [
            FACTS["beginning"],
            filler * 180,
            FACTS["middle"],
            filler * 180,
            FACTS["end"],
        ]
    )


def test_long_unseen_text_retrieves_facts_from_beginning_middle_and_end():
    payload = _long_unseen_document().encode("utf-8")
    extracted = extract_uploaded_document(
        filename="unseen_long_policy.txt",
        payload=payload,
        mime_type="text/plain",
    )

    assert len(payload) > 40_000
    assert len(extracted.chunks) > 30
    assert [chunk.chunk_index for chunk in extracted.chunks] == list(
        range(len(extracted.chunks))
    )

    documents = [
        LexicalDocument(
            document_id=f"chunk-{chunk.chunk_index}",
            content=chunk.content,
            metadata={"locator": chunk.locator},
        )
        for chunk in extracted.chunks
    ]
    retriever = BM25Retriever(documents)

    checks = [
        ("ALPHA 2719", FACTS["beginning"]),
        ("chu kỳ kiểm kê 37 ngày", FACTS["middle"]),
        ("ngưỡng phê duyệt 842 triệu đồng", FACTS["end"]),
    ]
    for query, expected_fact in checks:
        result = retriever.retrieve(query, top_k=1)
        assert result
        assert expected_fact in result[0].document.content
        assert result[0].score > 0


def test_upload_larger_than_15_mb_is_rejected_before_extraction():
    with pytest.raises(IngestionError, match="15 MB"):
        extract_uploaded_document(
            filename="oversized.txt",
            payload=b"x" * (MAX_UPLOAD_BYTES + 1),
            mime_type="text/plain",
        )
