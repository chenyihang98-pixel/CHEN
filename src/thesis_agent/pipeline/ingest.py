"""本地论文文档的 ingest 流程模块。"""

from __future__ import annotations

import json
from pathlib import Path

from thesis_agent.language import normalize_document_language
from thesis_agent.corpus.internal_pdf_loader import load_internal_pdf_documents
from thesis_agent.loaders.markdown_loader import load_markdown_documents
from thesis_agent.loaders.pdf_loader import load_pdf_documents
from thesis_agent.privacy.pii import assert_no_pii
from thesis_agent.processing.chunker import chunk_text


def ingest_documents(
    input_dir: Path,
    chunks_output: Path,
    metadata_output: Path,
    input_type: str = "auto",
    language: str = "ja",
    catalog_path: Path | None = None,
) -> dict:
    """Load supported local documents, chunk them, and export JSONL artifacts."""
    normalized_language = normalize_document_language(language)
    normalized_input_type = input_type.strip().lower()
    if normalized_input_type not in {"auto", "markdown", "pdf"}:
        raise ValueError(f"Unsupported input type: {input_type}")

    documents = []
    is_internal_catalog = catalog_path is not None
    if normalized_input_type in {"auto", "markdown"} and not is_internal_catalog:
        documents.extend(load_markdown_documents(input_dir=input_dir, language=normalized_language))
    if normalized_input_type in {"auto", "pdf"} and not is_internal_catalog:
        documents.extend(load_pdf_documents(input_dir=input_dir, language=normalized_language))
    if normalized_input_type == "pdf" and is_internal_catalog:
        documents.extend(load_internal_pdf_documents(catalog_path=catalog_path))
    if not documents:
        raise ValueError("No supported documents found in the input directory")

    all_chunks = []
    chunks_output.parent.mkdir(parents=True, exist_ok=True)
    metadata_output.parent.mkdir(parents=True, exist_ok=True)

    with metadata_output.open("w", encoding="utf-8") as metadata_file:
        for document in documents:
            if not is_internal_catalog:
                assert_no_pii(document.text)
            metadata_record = {
                "doc_id": document.doc_id,
                "title": document.title,
                "abstract": document.abstract,
                "keywords": document.keywords,
                "year": document.year,
                "major": document.major,
                "source_type": document.source_type,
                "source_name": document.source_name,
                "document_language": document.document_language,
            }
            if is_internal_catalog:
                metadata_record.update(
                    {
                        "author_name": document.author_name,
                        "student_id": document.student_id,
                        "advisor_name": document.advisor_name,
                        "original_filename": document.original_filename,
                        "pdf_path": document.pdf_path,
                    }
                )
            metadata_file.write(json.dumps(metadata_record, ensure_ascii=False) + "\n")

    with chunks_output.open("w", encoding="utf-8") as chunk_file:
        for document in documents:
            chunks = chunk_text(document.text, doc_id=document.doc_id, title=document.title)
            for chunk in chunks:
                if not is_internal_catalog:
                    assert_no_pii(chunk.text)
                metadata = {
                    **chunk.metadata,
                    "author_name": document.author_name,
                    "advisor_name": document.advisor_name,
                    "year": document.year,
                    "pdf_path": document.pdf_path,
                    "original_filename": document.original_filename,
                    "source_type": document.source_type,
                }
                chunk_record = {
                    "chunk_id": chunk.chunk_id,
                    "doc_id": chunk.doc_id,
                    "title": chunk.title,
                    "text": chunk.text,
                    "metadata": metadata,
                }
                chunk_file.write(json.dumps(chunk_record, ensure_ascii=False) + "\n")
                all_chunks.append(chunk_record)

    return {
        "document_count": len(documents),
        "chunk_count": len(all_chunks),
        "input_type": normalized_input_type,
        "language": normalized_language,
        "chunks_output": chunks_output.as_posix(),
        "metadata_output": metadata_output.as_posix(),
        "catalog_path": catalog_path.as_posix() if catalog_path else "",
    }


def ingest_samples(input_dir: Path, chunks_output: Path, metadata_output: Path) -> dict:
    """Backward-compatible wrapper for Markdown sample ingest."""
    return ingest_documents(
        input_dir=input_dir,
        chunks_output=chunks_output,
        metadata_output=metadata_output,
        input_type="markdown",
        language="auto",
    )
