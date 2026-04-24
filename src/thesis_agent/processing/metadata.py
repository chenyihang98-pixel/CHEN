"""从 Markdown 或 text-based PDF 文本提取 metadata 的模块。"""

from __future__ import annotations

import re

from thesis_agent.language import detect_document_language, get_metadata_labels, normalize_document_language


def _normalize_label(label: str) -> str:
    return label.strip().strip("#").strip().strip("：:").lower()


def _extract_sections(text: str, labels: dict[str, set[str]]) -> dict[str, str]:
    sections: dict[str, str] = {}
    current_key: str | None = None
    buffer: list[str] = []
    normalized_aliases = {key: {alias.lower() for alias in aliases} for key, aliases in labels.items()}

    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        matched_key = None

        if line.startswith("#"):
            label = _normalize_label(line)
            for key, aliases in normalized_aliases.items():
                if label in aliases:
                    matched_key = key
                    break
        elif "：" in line or ":" in line:
            candidate_label = _normalize_label(line.split("：", 1)[0].split(":", 1)[0])
            for key, aliases in normalized_aliases.items():
                if candidate_label in aliases:
                    matched_key = key
                    break
            if matched_key is not None:
                if current_key is not None:
                    sections[current_key] = "\n".join(buffer).strip()
                current_key = matched_key
                remainder = line.split("：", 1)[1] if "：" in line else line.split(":", 1)[1]
                buffer = [remainder.strip()] if remainder.strip() else []
                continue

        if matched_key is not None:
            if current_key is not None:
                sections[current_key] = "\n".join(buffer).strip()
            current_key = matched_key
            buffer = []
            continue

        if current_key is not None:
            buffer.append(raw_line.strip())

    if current_key is not None:
        sections[current_key] = "\n".join(buffer).strip()

    return sections


def _split_keywords(value: str) -> list[str]:
    if not value:
        return []

    parts = re.split(r"[，,、;；]", value)
    return [part.strip() for part in parts if part.strip()]


def extract_metadata_from_markdown(text: str, source_name: str, language: str = "auto") -> dict:
    """Extract best-effort metadata from a synthetic thesis document text."""
    normalized_language = normalize_document_language(language)
    effective_language = detect_document_language(text) if normalized_language == "auto" else normalized_language
    sections = _extract_sections(text, get_metadata_labels(effective_language))
    source_type = "markdown_sample" if source_name.lower().endswith(".md") else "pdf_sample"

    return {
        "title": sections.get("title", ""),
        "abstract": sections.get("abstract", ""),
        "keywords": _split_keywords(sections.get("keywords", "")),
        "year": sections.get("year", ""),
        "major": sections.get("major", ""),
        "source_type": source_type,
        "document_language": effective_language,
    }
