"""本地论文处理的文档语言辅助模块。"""

from __future__ import annotations

import re


SUPPORTED_DOCUMENT_LANGUAGES = {"auto", "ja", "zh", "en"}

JAPANESE_KANA_PATTERN = re.compile(r"[\u3040-\u30ff]")
CHINESE_HINT_PATTERN = re.compile(r"[论文题摘要关键词专业章节概要标题]")


def normalize_document_language(value: str | None) -> str:
    """Normalize and validate a configured document language."""
    if value is None:
        return "ja"

    normalized = value.strip().lower()
    if normalized not in SUPPORTED_DOCUMENT_LANGUAGES:
        raise ValueError(f"Unsupported document language: {value}")
    return normalized


def detect_document_language(text: str) -> str:
    """Detect a likely language using a small deterministic heuristic."""
    if JAPANESE_KANA_PATTERN.search(text):
        return "ja"
    if CHINESE_HINT_PATTERN.search(text):
        return "zh"
    return "en"


def get_metadata_labels(language: str) -> dict[str, set[str]]:
    """Return supported metadata labels for the requested language."""
    normalized = normalize_document_language(language)

    english = {
        "title": {"title"},
        "abstract": {"abstract"},
        "keywords": {"keywords", "keyword"},
        "year": {"year"},
        "major": {"major"},
        "outline": {"outline"},
    }
    chinese = {
        "title": {"题目", "标题"},
        "abstract": {"摘要"},
        "keywords": {"关键词"},
        "year": {"年份"},
        "major": {"专业"},
        "outline": {"章节概要"},
    }
    japanese = {
        "title": {"タイトル", "題目"},
        "abstract": {"要旨", "概要"},
        "keywords": {"キーワード"},
        "year": {"年度", "年"},
        "major": {"専攻", "学科"},
        "outline": {"章構成", "目次"},
    }

    if normalized == "ja":
        return {key: japanese[key] | english[key] for key in english}
    if normalized == "zh":
        return {key: chinese[key] | english[key] for key in english}
    if normalized == "en":
        return english
    return {key: english[key] | chinese[key] | japanese[key] for key in english}


def get_pii_labels(language: str) -> dict[str, set[str]]:
    """Return supported PII label hints for the requested language."""
    normalized = normalize_document_language(language)

    english = {
        "student_id": {"student id", "student number"},
        "student_name": {"student name", "name"},
        "supervisor": {"supervisor", "advisor"},
        "email": {"email", "mail"},
        "phone": {"phone", "telephone"},
        "affiliation": {"affiliation", "department", "laboratory"},
    }
    chinese = {
        "student_id": {"学号"},
        "student_name": {"学生姓名"},
        "supervisor": {"指导教师", "导师"},
        "email": {"邮箱", "电子邮箱"},
        "phone": {"电话", "手机号"},
        "affiliation": {"所属", "院系", "实验室"},
    }
    japanese = {
        "student_id": {"学籍番号", "学生番号"},
        "student_name": {"氏名", "学生氏名"},
        "supervisor": {"指導教員", "指導教授"},
        "email": {"メール"},
        "phone": {"電話番号"},
        "affiliation": {"所属", "研究室"},
    }

    if normalized == "ja":
        return {key: japanese[key] | english[key] for key in english}
    if normalized == "zh":
        return {key: chinese[key] | english[key] for key in english}
    if normalized == "en":
        return english
    return {key: english[key] | chinese[key] | japanese[key] for key in english}
