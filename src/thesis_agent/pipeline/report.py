"""生成本地确定性主题报告的流程模块。"""

from __future__ import annotations

from pathlib import Path

from thesis_agent.llm.mock import MockLLM
from thesis_agent.privacy.pii import assert_no_pii, scan_pii
from thesis_agent.tools.search import search_thesis
from thesis_agent.tools.topic import compare_topic


WORKSPACE_ROOT = Path.cwd().resolve()
FORBIDDEN_PARTS = {"raw", "private", "anonymized"}


def _validate_output_path(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("Refusing to write outside the project workspace") from exc

    if any(part.lower() in FORBIDDEN_PARTS for part in resolved.parts):
        raise ValueError("Refusing to write into a forbidden private data directory")
    return resolved


def _display_output_path(path: Path) -> str:
    """Return a workspace-relative path for user-facing output."""
    try:
        return path.relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return path.name


def generate_topic_report(
    index_path: Path,
    topic: str,
    top_k: int = 5,
    language: str = "ja",
    output_path: Path | None = None,
) -> dict:
    """Generate a deterministic local topic report."""
    if scan_pii(topic):
        raise ValueError("PII detected in topic. Please remove personal or sensitive information before report generation.")

    topic_result = compare_topic(index_path=index_path, topic=topic, top_k=top_k)
    if not topic_result.ok:
        raise ValueError("; ".join(topic_result.errors))

    search_result = search_thesis(index_path=index_path, query=topic, top_k=top_k)
    if not search_result.ok:
        raise ValueError("; ".join(search_result.errors))

    mock_llm = MockLLM()
    report = mock_llm.generate_topic_report(
        topic=topic,
        topic_analysis=topic_result.data,
        search_results=search_result.data["results"],
        structure_analysis=None,
        language=language,
    )
    assert_no_pii(report)

    final_output = None
    if output_path is not None:
        safe_path = _validate_output_path(output_path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        safe_path.write_text(report, encoding="utf-8")
        final_output = _display_output_path(safe_path)

    return {
        "topic": topic,
        "risk_level": topic_result.data["risk_level"],
        "risk_score": topic_result.data["risk_score"],
        "result_count": len(search_result.data["results"]),
        "output_path": final_output,
        "report": report,
    }
