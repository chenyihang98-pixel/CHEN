"""本地 TF-IDF 检索流程辅助模块。"""

from __future__ import annotations

from pathlib import Path

from thesis_agent.language import normalize_document_language
from thesis_agent.retrieval.io import load_chunks_jsonl
from thesis_agent.retrieval.models import RetrievalConfig, SearchResult
from thesis_agent.retrieval.tfidf import TfidfRetriever


def build_tfidf_index(
    chunks_path: Path,
    index_output: Path,
    language: str = "ja",
    analyzer: str = "char",
    ngram_min: int = 2,
    ngram_max: int = 5,
) -> dict:
    """Build and persist a local TF-IDF index from chunk JSONL."""
    chunks = load_chunks_jsonl(chunks_path)
    config = RetrievalConfig(
        analyzer=analyzer,
        ngram_min=ngram_min,
        ngram_max=ngram_max,
        language=normalize_document_language(language),
    )

    retriever = TfidfRetriever(config=config).fit(chunks)
    retriever.save(index_output)

    return {
        "chunk_count": len(chunks),
        "index_output": index_output.as_posix(),
        "analyzer": analyzer,
        "ngram_range": (ngram_min, ngram_max),
        "language": config.language,
    }


def search_tfidf_index(
    index_path: Path,
    query: str,
    top_k: int = 5,
) -> list[SearchResult]:
    """Search a persisted local TF-IDF index."""
    retriever = TfidfRetriever.load(index_path)
    return retriever.search(query=query, top_k=top_k)
