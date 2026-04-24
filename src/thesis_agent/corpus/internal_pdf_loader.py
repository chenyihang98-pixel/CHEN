"""保留 metadata 的内部 text-based PDF 加载模块。"""

from __future__ import annotations

from pathlib import Path

from thesis_agent.corpus.catalog import load_catalog
from thesis_agent.corpus.metadata_extractors import extract_pdf_text
from thesis_agent.corpus.retrieval_text import build_retrieval_text
from thesis_agent.models import ThesisDocument


def load_internal_pdf_documents(catalog_path: Path) -> list[ThesisDocument]:
    """Load internal PDF documents from a catalog, preserving display metadata."""
    documents: list[ThesisDocument] = []
    for record in load_catalog(catalog_path):
        if record.get("status", "active") != "active":
            continue

        pdf_path = Path(record["pdf_path"])
        if not pdf_path.exists():
            continue

        raw_text = extract_pdf_text(pdf_path)
        retrieval_text = build_retrieval_text(raw_text)
        if not retrieval_text:
            raise ValueError(f"No retrieval text could be extracted from PDF: {pdf_path.name}")

        documents.append(
            ThesisDocument(
                doc_id=record["doc_id"],
                title=record.get("title", ""),
                abstract="",
                keywords=[],
                year=record.get("year", ""),
                major="",
                source_type="internal_pdf",
                source_name=record.get("doc_id", ""),
                document_language="ja",
                text=retrieval_text,
                author_name=record.get("author_name", ""),
                student_id=record.get("student_id", ""),
                advisor_name=record.get("advisor_name", ""),
                original_filename=record.get("original_filename", ""),
                pdf_path=record.get("pdf_path", ""),
            )
        )
    return documents
