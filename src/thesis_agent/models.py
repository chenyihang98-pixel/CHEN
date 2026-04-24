"""本地论文处理流程使用的轻量数据结构。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ThesisDocument:
    """Structured representation of one synthetic thesis sample."""

    doc_id: str
    title: str
    abstract: str
    keywords: list[str]
    year: str
    major: str
    source_type: str
    source_name: str
    document_language: str
    text: str
    author_name: str = ""
    student_id: str = ""
    advisor_name: str = ""
    original_filename: str = ""
    pdf_path: str = ""


@dataclass(frozen=True)
class ThesisChunk:
    """Character-based chunk for downstream local processing."""

    chunk_id: str
    doc_id: str
    title: str
    text: str
    metadata: dict = field(default_factory=dict)
