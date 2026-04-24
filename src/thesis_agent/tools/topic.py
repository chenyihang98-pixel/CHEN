"""主题比较与本地风险启发式分析模块。"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from thesis_agent.privacy.pii import scan_pii
from thesis_agent.tools.schemas import ToolResult, TopicRiskAnalysis
from thesis_agent.tools.search import search_thesis


def _build_recommendations(risk_level: str) -> list[str]:
    if risk_level == "high":
        return [
            "上位の類似テーマとの差分を明確にし、対象範囲や評価条件を具体化してください。",
            "キーワードの重複が大きいため、独自の利用場面や制約条件を追加することを検討してください。",
        ]
    if risk_level == "medium":
        return [
            "関連研究と重なる観点を整理し、比較軸を先に定義してください。",
            "目的、対象データ、評価観点のいずれかを限定すると独自性を示しやすくなります。",
        ]
    return [
        "現時点では重複度は高くありませんが、関連研究との差分は引き続き明文化してください。",
        "検索結果を参考に、対象読者や適用場面を具体化すると計画が安定します。",
    ]


def compare_topic(
    index_path: Path,
    topic: str,
    top_k: int = 5,
    allow_pii_query: bool = False,
) -> ToolResult:
    """Compare a topic against retrieved synthetic thesis chunks."""
    if not topic or not topic.strip():
        return ToolResult(tool_name="compare_topic", ok=False, data={}, errors=["Topic must not be empty."])

    pii_findings = scan_pii(topic)
    if pii_findings and not allow_pii_query:
        return ToolResult(
            tool_name="compare_topic",
            ok=False,
            data={},
            errors=["PII detected in topic. Please remove personal or sensitive information before analysis."],
        )

    search_result = search_thesis(index_path=index_path, query=topic, top_k=top_k, allow_pii_query=allow_pii_query)
    if not search_result.ok:
        return ToolResult(tool_name="compare_topic", ok=False, data={}, errors=search_result.errors)

    results = search_result.data["results"]
    top_score = float(results[0]["score"]) if results else 0.0
    if top_score >= 0.18:
        risk_level = "high"
    elif top_score >= 0.07:
        risk_level = "medium"
    else:
        risk_level = "low"

    analysis = TopicRiskAnalysis(
        topic=topic,
        risk_level=risk_level,
        risk_score=round(top_score, 4),
        top_similarity_score=round(top_score, 4),
        similar_count=len(results),
        citations=[result["citation"] for result in results],
        recommendations=_build_recommendations(risk_level),
    )

    data = asdict(analysis)
    data["references"] = results
    data["note"] = "This is only a topic similarity / overlap signal, not plagiarism detection."
    return ToolResult(tool_name="compare_topic", ok=True, data=data)
