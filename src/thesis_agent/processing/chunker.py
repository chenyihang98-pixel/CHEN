"""论文文档的字符级 chunk 切分模块。"""

from __future__ import annotations

from thesis_agent.models import ThesisChunk


def chunk_text(
    text: str,
    doc_id: str,
    title: str,
    chunk_size: int = 500,
    overlap: int = 80,
) -> list[ThesisChunk]:
    """Split text into overlapping character chunks."""
    if not text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    chunks: list[ThesisChunk] = []
    start = 0
    chunk_index = 1
    step = chunk_size - overlap

    while start < len(text):
        chunk_body = text[start : start + chunk_size].strip()
        if chunk_body:
            chunk_id = f"{doc_id}_chunk_{chunk_index:03d}"
            chunks.append(
                ThesisChunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    title=title,
                    text=chunk_body,
                    metadata={
                        "doc_id": doc_id,
                        "title": title,
                        "chunk_index": chunk_index,
                    },
                )
            )
            chunk_index += 1
        start += step

    return chunks
