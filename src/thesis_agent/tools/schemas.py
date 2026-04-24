"""本地 tool 层使用的轻量 schema。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolResult:
    """Generic wrapper for tool execution results."""

    tool_name: str
    ok: bool
    data: dict
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class TopicRiskAnalysis:
    """Deterministic topic overlap analysis summary."""

    topic: str
    risk_level: str
    risk_score: float
    top_similarity_score: float
    similar_count: int
    citations: list[str]
    recommendations: list[str]


@dataclass(frozen=True)
class StructureAnalysis:
    """Simple structure completeness analysis."""

    language: str
    score: float
    present_sections: list[str]
    missing_sections: list[str]
    suggestions: list[str]


@dataclass(frozen=True)
class ReportSection:
    """One section of a locally generated report."""

    title: str
    body: str
