"""论文内容的本地 PII 简易扫描模块。"""

from __future__ import annotations

import re

from thesis_agent.language import get_pii_labels


BASE_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"(?<!\d)(?:(?:\+?86[- ]?)?1[3-9]\d{9}|(?:0[789]0[- ]?\d{4}[- ]?\d{4}))(?!\d)"),
    "id_number": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "windows_path": re.compile(r"\b[A-Za-z]:\\(?:[^\\\r\n]+\\)*[^\\\r\n]*"),
    "unix_path": re.compile(r"(?<!\w)/(?:home|Users|mnt|var|opt|srv|tmp)/[^\s]+"),
}

LABELLED_PATTERN_KEYS = {
    "student_id": "student_id_label",
    "student_name": "student_name_label",
    "supervisor": "advisor_label",
    "email": "email_label",
    "phone": "phone_label",
    "affiliation": "affiliation_label",
}


def _build_label_patterns() -> dict[str, re.Pattern[str]]:
    patterns: dict[str, re.Pattern[str]] = {}
    label_sets = get_pii_labels("auto")

    for label_type, labels in label_sets.items():
        escaped = "|".join(sorted((re.escape(label) for label in labels), key=len, reverse=True))
        patterns[LABELLED_PATTERN_KEYS[label_type]] = re.compile(
            rf"(?:{escaped})\s*[:：]?\s*[^\n]{{1,40}}",
            re.IGNORECASE,
        )

    return patterns


PII_PATTERNS: dict[str, re.Pattern[str]] = BASE_PII_PATTERNS | _build_label_patterns()


def scan_pii(text: str) -> list[dict]:
    """Return all simple PII matches found in the input text."""
    findings: list[dict] = []
    if not text:
        return findings

    for pii_type, pattern in PII_PATTERNS.items():
        for match in pattern.finditer(text):
            findings.append(
                {
                    "type": pii_type,
                    "match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                }
            )
    return findings


def anonymize_text(text: str) -> str:
    """Mask simple PII patterns in text."""
    anonymized = text
    for pii_type, pattern in PII_PATTERNS.items():
        anonymized = pattern.sub(f"[REDACTED_{pii_type.upper()}]", anonymized)
    return anonymized


def assert_no_pii(text: str) -> None:
    """Raise an error when PII-like patterns are detected."""
    findings = scan_pii(text)
    if findings:
        types = ", ".join(sorted({finding["type"] for finding in findings}))
        raise ValueError(f"PII detected: {types}")
