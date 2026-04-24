"""本地论文样例的结构分析 tool 模块。"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from thesis_agent.language import detect_document_language, normalize_document_language
from thesis_agent.privacy.pii import scan_pii
from thesis_agent.tools.schemas import StructureAnalysis, ToolResult


WORKSPACE_ROOT = Path.cwd().resolve()
FORBIDDEN_PARTS = {"raw", "private", "anonymized"}

SECTION_LABELS = {
    "ja": ["タイトル", "要旨", "キーワード", "年度", "専攻", "章構成"],
    "zh": ["题目", "摘要", "关键词", "年份", "专业", "章节概要"],
    "en": ["title", "abstract", "keywords", "year", "major", "outline"],
}


def _resolve_language(language: str, text: str) -> str:
    normalized = normalize_document_language(language)
    return detect_document_language(text) if normalized == "auto" else normalized


def _analyze_structure(text: str, language: str) -> StructureAnalysis:
    effective_language = _resolve_language(language, text)
    required_sections = SECTION_LABELS[effective_language]
    present_sections = [section for section in required_sections if section in text]
    missing_sections = [section for section in required_sections if section not in text]
    score = len(present_sections) / len(required_sections)

    suggestions = []
    if missing_sections:
        suggestions.append("不足している見出しを追加し、基本構成を揃えてください。")
    else:
        suggestions.append("主要見出しは揃っています。要旨と章構成の具体性を維持してください。")

    return StructureAnalysis(
        language=effective_language,
        score=round(score, 4),
        present_sections=present_sections,
        missing_sections=missing_sections,
        suggestions=suggestions,
    )


def analyze_structure_text(
    text: str,
    language: str = "ja",
) -> ToolResult:
    """Analyze structure completeness from raw text."""
    pii_findings = scan_pii(text)
    if pii_findings:
        return ToolResult(
            tool_name="analyze_structure",
            ok=False,
            data={},
            errors=["PII detected in text. Please remove personal or sensitive information before analysis."],
        )

    analysis = _analyze_structure(text, language)
    return ToolResult(tool_name="analyze_structure", ok=True, data=asdict(analysis))


def analyze_structure_file(
    path: Path,
    language: str = "ja",
) -> ToolResult:
    """Analyze structure completeness from a safe local file."""
    resolved = path.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return ToolResult(
            tool_name="analyze_structure",
            ok=False,
            data={},
            errors=["Refusing to read files outside the project workspace."],
        )

    if any(part.lower() in FORBIDDEN_PARTS for part in resolved.parts):
        return ToolResult(
            tool_name="analyze_structure",
            ok=False,
            data={},
            errors=["Refusing to read from a forbidden private data directory."],
        )

    text = resolved.read_text(encoding="utf-8")
    return analyze_structure_text(text=text, language=language)
