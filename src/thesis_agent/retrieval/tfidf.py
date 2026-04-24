"""面向论文 chunk 的本地 TF-IDF 检索模块。"""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from thesis_agent.retrieval.models import RetrievalConfig, SearchResult


class TfidfRetriever:
    """A simple local TF-IDF retriever over chunk text."""

    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self.config = config or RetrievalConfig()
        self.vectorizer: TfidfVectorizer | None = None
        self.matrix = None
        self.chunks: list[dict] = []

    def fit(self, chunks: list[dict]) -> "TfidfRetriever":
        """Fit a TF-IDF model over chunk text."""
        if not chunks:
            raise ValueError("Cannot fit retriever with no chunks")

        texts = []
        for chunk in chunks:
            text = chunk.get("text", "")
            if not text:
                raise ValueError("Every chunk must include non-empty text")
            texts.append(text)

        self.vectorizer = TfidfVectorizer(
            analyzer=self.config.analyzer,
            ngram_range=(self.config.ngram_min, self.config.ngram_max),
            lowercase=self.config.lowercase,
        )
        self.matrix = self.vectorizer.fit_transform(texts)
        self.chunks = chunks
        return self

    def search(self, query: str, top_k: int | None = None) -> list[SearchResult]:
        """Search the fitted TF-IDF index and return ranked results."""
        if self.vectorizer is None or self.matrix is None or not self.chunks:
            raise ValueError("Retriever must be fit before search")
        if not query or not query.strip():
            raise ValueError("Query must not be empty")

        query_vector = self.vectorizer.transform([query])
        scores = (self.matrix @ query_vector.T).toarray().ravel()

        k = min(top_k or self.config.top_k, len(self.chunks))
        ranked_indices = np.argsort(scores)[::-1][:k]

        results: list[SearchResult] = []
        for rank, index in enumerate(ranked_indices, start=1):
            chunk = self.chunks[int(index)]
            results.append(
                SearchResult(
                    rank=rank,
                    score=float(scores[int(index)]),
                    chunk_id=chunk["chunk_id"],
                    doc_id=chunk["doc_id"],
                    title=chunk["title"],
                    text=chunk["text"],
                    metadata=chunk["metadata"],
                    citation=f"{chunk['doc_id']}#{chunk['chunk_id']}",
                )
            )
        return results

    def save(self, path: Path) -> None:
        """Serialize the fitted retriever to disk."""
        if self.vectorizer is None or self.matrix is None:
            raise ValueError("Retriever must be fit before save")

        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "config": self.config,
            "vectorizer": self.vectorizer,
            "matrix": self.matrix,
            "chunks": self.chunks,
        }
        with path.open("wb") as handle:
            pickle.dump(payload, handle)

    @classmethod
    def load(cls, path: Path) -> "TfidfRetriever":
        """Load a serialized retriever from disk."""
        if not path.exists():
            raise ValueError(f"Index file does not exist: {path}")

        with path.open("rb") as handle:
            payload = pickle.load(handle)

        retriever = cls(config=payload["config"])
        retriever.vectorizer = payload["vectorizer"]
        retriever.matrix = payload["matrix"]
        retriever.chunks = payload["chunks"]
        return retriever
