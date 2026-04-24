"""Streamlit UI 辅助模块。"""

from thesis_agent.ui.services import (
    build_pdf_action_metadata,
    ensure_demo_assets,
    list_demo_samples,
    persist_search_result,
    persist_topic_result,
    rebuild_demo_assets,
    run_search,
    run_structure_check,
    run_topic_analysis,
)

__all__ = [
    "ensure_demo_assets",
    "build_pdf_action_metadata",
    "list_demo_samples",
    "persist_search_result",
    "persist_topic_result",
    "rebuild_demo_assets",
    "run_search",
    "run_structure_check",
    "run_topic_analysis",
]
