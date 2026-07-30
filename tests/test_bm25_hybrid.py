import pytest

from src.bm25_retriever import BM25Retriever, LexicalDocument, tokenize_vietnamese
from src.hybrid_retriever import RankedCandidate, reciprocal_rank_fusion


def test_vietnamese_tokenizer_is_case_insensitive():
    assert tokenize_vietnamese("Chính SÁCH nghỉ-phép") == [
        "chính",
        "sách",
        "nghỉ",
        "phép",
    ]


def test_bm25_ranks_matching_passage_first_deterministically():
    documents = [
        LexicalDocument("finance", "Quy trình thanh toán hóa đơn."),
        LexicalDocument("hr", "Chính sách nghỉ phép của nhân viên."),
        LexicalDocument("it", "Quy định cấp tài khoản hệ thống."),
    ]
    retriever = BM25Retriever(documents)

    first = retriever.retrieve("nhân viên được nghỉ phép thế nào", top_k=3)
    second = retriever.retrieve("nhân viên được nghỉ phép thế nào", top_k=3)

    assert [result.document.document_id for result in first] == [
        result.document.document_id for result in second
    ]
    assert first[0].document.document_id == "hr"
    assert first[0].score > first[1].score


def test_rrf_rewards_candidates_found_by_both_rankers():
    dense = [
        RankedCandidate("a", "A"),
        RankedCandidate("shared", "Shared"),
        RankedCandidate("b", "B"),
    ]
    bm25 = [
        RankedCandidate("c", "C"),
        RankedCandidate("shared", "Shared"),
        RankedCandidate("d", "D"),
    ]

    fused = reciprocal_rank_fusion({"dense": dense, "bm25": bm25}, top_k=5)

    assert fused[0].candidate.candidate_id == "shared"
    assert fused[0].source_ranks == {"dense": 2, "bm25": 2}


def test_rrf_rejects_negative_rank_constant():
    with pytest.raises(ValueError, match="rank_constant"):
        reciprocal_rank_fusion({}, rank_constant=-1)
