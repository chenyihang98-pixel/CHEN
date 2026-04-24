"""加载 text-based PDF 论文样例的模块。"""

from __future__ import annotations

from pathlib import Path

import pymupdf

from thesis_agent.language import normalize_document_language
from thesis_agent.models import ThesisDocument
from thesis_agent.privacy.pii import assert_no_pii
from thesis_agent.processing.cleaner import clean_markdown_text
from thesis_agent.processing.metadata import extract_metadata_from_markdown

from thesis_agent.loaders.markdown_loader import _validate_input_dir


def extract_text_from_pdf(pdf_path: Path, sort: bool = True) -> str:
    """Extract plain text from a text-based PDF using PyMuPDF."""
    with pymupdf.open(pdf_path) as document:
        page_texts = [page.get_text("text", sort=sort) for page in document]

    combined = "\n".join(page_texts).strip()
    if not combined:
        raise ValueError(f"No extractable text found in PDF: {pdf_path.name}")
    return combined


def load_pdf_documents(input_dir: Path, language: str = "ja") -> list[ThesisDocument]:
    """Load synthetic text-based PDF files from a local input directory."""
    base_dir = _validate_input_dir(input_dir)
    normalized_language = normalize_document_language(language)
    if not base_dir.exists():
        return []

    documents: list[ThesisDocument] = []
    pdf_files = sorted(path for path in base_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")

    for index, file_path in enumerate(pdf_files, start=1):
        raw_text = extract_text_from_pdf(file_path, sort=True)
        assert_no_pii(raw_text)

        metadata = extract_metadata_from_markdown(
            raw_text,
            source_name=file_path.name,
            language=normalized_language,
        )
        cleaned_text = clean_markdown_text(raw_text)
        assert_no_pii(cleaned_text)

        documents.append(
            ThesisDocument(
                doc_id=f"pdf_doc_{index:03d}",
                title=metadata.get("title", ""),
                abstract=metadata.get("abstract", ""),
                keywords=metadata.get("keywords", []),
                year=metadata.get("year", ""),
                major=metadata.get("major", ""),
                source_type="pdf_sample",
                source_name=file_path.name,
                document_language=metadata.get("document_language", normalized_language),
                text=cleaned_text,
            )
        )

    return documents
