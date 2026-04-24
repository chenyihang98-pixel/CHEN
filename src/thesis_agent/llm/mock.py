"""本地确定性 MockLLM 报告生成模块。"""

from __future__ import annotations

from thesis_agent.privacy.pii import assert_no_pii


class MockLLM:
    """A deterministic local mock report generator."""

    provider_name = "mock"

    def generate_topic_report(
        self,
        topic: str,
        topic_analysis: dict,
        search_results: list[dict],
        structure_analysis: dict | None = None,
        language: str = "ja",
    ) -> str:
        """Generate a deterministic Markdown topic report."""
        citations = topic_analysis.get("citations", [])
        recommendations = topic_analysis.get("recommendations", [])
        similarity_lines = [
            f"- {result['title']} ({result['citation']}, score={float(result['score']):.4f})"
            for result in search_results
        ] or ["- 類似候補は見つかりませんでした。"]

        structure_block = ""
        if structure_analysis:
            structure_block = (
                "\n## 構成チェック\n\n"
                f"- score: {float(structure_analysis.get('score', 0.0)):.4f}\n"
                f"- present_sections: {', '.join(structure_analysis.get('present_sections', []))}\n"
                f"- missing_sections: {', '.join(structure_analysis.get('missing_sections', [])) or 'なし'}\n"
            )

        report = "\n".join(
            [
                "# タイトル",
                "",
                f"{topic} に関するローカル分析レポート",
                "",
                "## 概要",
                "",
                f"このレポートは、ローカルのTF-IDF検索結果と決定的なテンプレート処理に基づいて生成されたMockレポートである。対象トピックは「{topic}」であり、上位類似候補の重なり度合いと整理の方向性を要約する。",
                "",
                "## 類似研究候補",
                "",
                *similarity_lines,
                "",
                "## リスク評価",
                "",
                f"- risk_level: {topic_analysis.get('risk_level', 'unknown')}",
                f"- risk_score: {float(topic_analysis.get('risk_score', 0.0)):.4f}",
                f"- top_similarity_score: {float(topic_analysis.get('top_similarity_score', 0.0)):.4f}",
                f"- similar_count: {topic_analysis.get('similar_count', 0)}",
                f"- note: {topic_analysis.get('note', 'This is only a topic similarity / overlap signal, not plagiarism detection.')}",
                "",
                "## 改善提案",
                "",
                *([f"- {item}" for item in recommendations] or ["- 追加の改善提案はありません。"]),
                "",
                "## 推奨される次のステップ",
                "",
                "- 関連研究との差分を対象範囲、評価条件、利用場面の観点で整理する。",
                "- タイトルと要旨に独自性を示す語を追加する。",
                "- 必要に応じて章構成を明示し、研究計画を具体化する。",
                structure_block,
                "",
                "## 引用",
                "",
                *([f"- {citation}" for citation in citations] or ["- 引用候補なし"]),
                "",
                "## 免責事項",
                "",
                "これはローカルのMockレポートであり、不正行為や剽窃の判定ではありません。",
            ]
        ).replace("\n\n\n", "\n\n")

        assert_no_pii(report)
        return report
