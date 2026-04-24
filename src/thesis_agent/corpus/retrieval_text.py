"""为语义检索准备内部 PDF 文本的模块。"""

from __future__ import annotations

import re


IDENTITY_LABELS = (
    "氏名",
    "学生氏名",
    "学籍番号",
    "学生番号",
    "指導教員",
    "指導教授",
    "指導教師",
    "所属",
    "研究室",
    "提出日",
)


def strip_acknowledgements(text: str) -> str:
    """Remove common acknowledgement sections from retrieval text."""
    pattern = re.compile(r"(謝辞|謝意|Acknowledgements?)(.|\n)*$", re.IGNORECASE)
    return pattern.sub("", text)


def build_retrieval_text(raw_text: str) -> str:
    """Remove identity-heavy lines so retrieval focuses on thesis content."""
    filtered_lines = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if any(label in stripped for label in IDENTITY_LABELS):
            continue
        filtered_lines.append(stripped)

    text = "\n".join(filtered_lines)
    text = strip_acknowledgements(text)
    return re.sub(r"\s+", " ", text).strip()
