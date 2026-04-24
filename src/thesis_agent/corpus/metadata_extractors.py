"""内部 text-based PDF 论文的 metadata 提取辅助模块。"""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf


FIELD_LABELS = {
    "title": ("タイトル", "題目", "論文題目", "Title"),
    "author_name": ("氏名", "学生氏名", "著者", "Author"),
    "student_id": ("学籍番号", "学生番号", "Student ID", "Student Number"),
    "advisor_name": ("指導教員", "指導教授", "指導教師", "Advisor", "Supervisor"),
    "year": ("年度", "提出年度", "Year"),
}


def extract_pdf_text(pdf_path: Path, max_pages: int | None = None) -> str:
    """Extract text from a text-based PDF without OCR."""
    with pymupdf.open(pdf_path) as document:
        page_count = len(document) if max_pages is None else min(len(document), max_pages)
        page_texts = [document[index].get_text("text", sort=True) for index in range(page_count)]
    return "\n".join(page_texts).strip()


def _extract_label_value(lines: list[str], labels: tuple[str, ...]) -> str:
    escaped = "|".join(re.escape(label) for label in labels)
    inline_pattern = re.compile(rf"^(?:{escaped})\s*[:：]\s*(.*)$", re.IGNORECASE)
    label_only_pattern = re.compile(rf"^(?:{escaped})\s*[:：]?\s*$", re.IGNORECASE)

    for index, line in enumerate(lines):
        match = inline_pattern.match(line)
        if match:
            value = match.group(1).strip()
            if value:
                return value
            for next_line in lines[index + 1 : index + 4]:
                if next_line.strip():
                    return next_line.strip()
        if label_only_pattern.match(line):
            for next_line in lines[index + 1 : index + 4]:
                if next_line.strip():
                    return next_line.strip()
    return ""


def _extract_year(lines: list[str]) -> str:
    labelled = _extract_label_value(lines, FIELD_LABELS["year"])
    match = re.search(r"(19|20)\d{2}", labelled)
    if match:
        return match.group(0)

    for line in lines[:80]:
        if any(label in line for label in ("年度", "提出日", "提出年度")):
            match = re.search(r"(19|20)\d{2}", line)
            if match:
                return match.group(0)
    return ""


def extract_internal_pdf_metadata(pdf_path: Path) -> dict:
    """Extract display metadata from the cover pages of a text-based Japanese thesis PDF."""
    cover_text = extract_pdf_text(pdf_path, max_pages=2)
    lines = [line.strip() for line in cover_text.splitlines() if line.strip()]

    metadata = {
        "title": _extract_label_value(lines, FIELD_LABELS["title"]),
        "author_name": _extract_label_value(lines, FIELD_LABELS["author_name"]),
        "student_id": _extract_label_value(lines, FIELD_LABELS["student_id"]),
        "advisor_name": _extract_label_value(lines, FIELD_LABELS["advisor_name"]),
        "year": _extract_year(lines),
    }

    if not metadata["title"] and lines:
        metadata["title"] = lines[0]
    return metadata
