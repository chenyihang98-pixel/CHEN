"""加载匿名 Markdown 论文样例的模块。"""

from __future__ import annotations

from pathlib import Path

from thesis_agent.language import normalize_document_language
from thesis_agent.models import ThesisDocument
from thesis_agent.privacy.pii import assert_no_pii
from thesis_agent.processing.cleaner import clean_markdown_text
from thesis_agent.processing.metadata import extract_metadata_from_markdown


FORBIDDEN_DIR_NAMES = {"raw", "private", "anonymized"}
WORKSPACE_ROOT = Path.cwd().resolve()


def _validate_input_dir(input_dir: Path) -> Path:
    resolved = input_dir.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("Refusing to read outside the project workspace") from exc
    parts_lower = {part.lower() for part in resolved.parts}
    if any(part in FORBIDDEN_DIR_NAMES for part in parts_lower):
        raise ValueError("Refusing to read from a forbidden data directory")
    return resolved


def load_markdown_documents(input_dir: Path = Path("data/samples"), language: str = "auto") -> list[ThesisDocument]:
    """Load synthetic Markdown files from a local input directory."""
    base_dir = _validate_input_dir(input_dir)
    normalized_language = normalize_document_language(language)
    if not base_dir.exists():
        return []

    documents: list[ThesisDocument] = []
    markdown_files = sorted(path for path in base_dir.iterdir() if path.is_file() and path.suffix.lower() == ".md")

    for index, file_path in enumerate(markdown_files, start=1):
        raw_text = file_path.read_text(encoding="utf-8")
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
                doc_id=f"demo_doc_{index:03d}",
                title=metadata.get("title", ""),
                abstract=metadata.get("abstract", ""),
                keywords=metadata.get("keywords", []),
                year=metadata.get("year", ""),
                major=metadata.get("major", ""),
                source_type=metadata.get("source_type", "markdown_sample"),
                source_name=file_path.name,
                document_language=metadata.get("document_language", normalized_language),
                text=cleaned_text,
            )
        )

    return documents
