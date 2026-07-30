"""Small deterministic BM25 baseline for Vietnamese enterprise passages."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import math
import re
from typing import Any, Dict, Iterable, List


def tokenize_vietnamese(text: str) -> List[str]:
    """Lowercase Unicode word tokenizer used by both index and query."""
    return re.findall(r"\w+", text.casefold(), flags=re.UNICODE)


@dataclass(frozen=True)
class LexicalDocument:
    document_id: str
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BM25Result:
    document: LexicalDocument
    score: float
    rank: int


class BM25Retriever:
    """In-memory BM25 with a fixed tokenizer and explicit parameters."""

    def __init__(
        self,
        documents: Iterable[LexicalDocument],
        *,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        self.documents = list(documents)
        self.k1 = float(k1)
        self.b = float(b)
        self._tokens = [tokenize_vietnamese(doc.content) for doc in self.documents]
        self._term_frequencies = [Counter(tokens) for tokens in self._tokens]
        self._document_lengths = [len(tokens) for tokens in self._tokens]
        self._average_length = (
            sum(self._document_lengths) / len(self._document_lengths)
            if self._document_lengths
            else 0.0
        )
        self._document_frequency = self._build_document_frequency(self._tokens)

    @staticmethod
    def _build_document_frequency(token_rows: Iterable[List[str]]) -> Counter[str]:
        frequencies: Counter[str] = Counter()
        for tokens in token_rows:
            frequencies.update(set(tokens))
        return frequencies

    def _idf(self, token: str) -> float:
        document_count = len(self.documents)
        document_frequency = self._document_frequency.get(token, 0)
        return math.log(
            1.0
            + (document_count - document_frequency + 0.5)
            / (document_frequency + 0.5)
        )

    def _score(self, query_tokens: Iterable[str], index: int) -> float:
        if not self.documents or self._average_length <= 0:
            return 0.0

        term_frequency = self._term_frequencies[index]
        document_length = self._document_lengths[index]
        score = 0.0
        for token in set(query_tokens):
            frequency = term_frequency.get(token, 0)
            if frequency <= 0:
                continue
            denominator = frequency + self.k1 * (
                1.0 - self.b + self.b * document_length / self._average_length
            )
            score += self._idf(token) * (
                frequency * (self.k1 + 1.0) / denominator
            )
        return score

    def retrieve(self, query: str, *, top_k: int = 20) -> List[BM25Result]:
        if top_k <= 0:
            return []
        query_tokens = tokenize_vietnamese(query)
        scored = [
            (self._score(query_tokens, index), document)
            for index, document in enumerate(self.documents)
        ]
        scored.sort(key=lambda item: (-item[0], item[1].document_id))
        return [
            BM25Result(document=document, score=score, rank=rank)
            for rank, (score, document) in enumerate(scored[:top_k], start=1)
        ]
