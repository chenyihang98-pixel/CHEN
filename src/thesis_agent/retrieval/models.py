"""本地 TF-IDF 检索的数据模型。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SearchResult:
    """One ranked retrieval result."""

    rank: int
    score: float
    chunk_id: str
    doc_id: str
    title: str
    text: str
    metadata: dict
    citation: str


@dataclass(frozen=True)
class RetrievalConfig:
    """Configuration for the local TF-IDF retriever."""

    analyzer: str = "char"
    ngram_min: int = 2
    ngram_max: int = 5
    lowercase: bool = False
    top_k: int = 5
    language: str = "ja"
