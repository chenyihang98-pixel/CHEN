"""本地运行配置读取工具。"""

from __future__ import annotations

import os
from dataclasses import dataclass

from thesis_agent.language import normalize_document_language


SUPPORTED_UI_LANGUAGES = {"zh", "en", "ja"}
SUPPORTED_KB_MODES = {"demo", "internal"}


def _parse_bool(value: str | None, default: bool = False) -> bool:
    """将常见环境变量字符串转换为 bool。"""
    if value is None:
        return default

    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "on"}


def _normalize_ui_language(value: str | None) -> str:
    if value is None:
        return "zh"

    normalized = value.strip().lower()
    if normalized not in SUPPORTED_UI_LANGUAGES:
        raise ValueError(f"Unsupported UI language: {value}")
    return normalized


def _normalize_kb_mode(value: str | None) -> str:
    if value is None:
        return "demo"

    normalized = value.strip().lower()
    if normalized not in SUPPORTED_KB_MODES:
        raise ValueError(f"Unsupported KB mode: {value}")
    return normalized


@dataclass(frozen=True)
class AppConfig:
    """应用运行所需的非敏感配置。"""

    llm_provider: str = "mock"
    retriever_type: str = "tfidf"
    allow_external_llm_for_private_data: bool = False
    document_language: str = "ja"
    ui_language: str = "zh"
    kb_mode: str = "demo"
    lab_pdf_root: str = ""
    lab_catalog_path: str = ""
    lab_chunks_path: str = ""
    lab_index_path: str = ""


def get_app_config() -> AppConfig:
    """从环境变量读取支持的非敏感配置。"""
    return AppConfig(
        llm_provider=os.getenv("LLM_PROVIDER", "mock"),
        retriever_type=os.getenv("RETRIEVER_TYPE", "tfidf"),
        allow_external_llm_for_private_data=_parse_bool(
            os.getenv("ALLOW_EXTERNAL_LLM_FOR_PRIVATE_DATA"),
            default=False,
        ),
        document_language=normalize_document_language(os.getenv("DOCUMENT_LANGUAGE", "ja")),
        ui_language=_normalize_ui_language(os.getenv("UI_LANGUAGE", "zh")),
        kb_mode=_normalize_kb_mode(os.getenv("KB_MODE", "demo")),
        lab_pdf_root=os.getenv("LAB_PDF_ROOT", ""),
        lab_catalog_path=os.getenv("LAB_CATALOG_PATH", ""),
        lab_chunks_path=os.getenv("LAB_CHUNKS_PATH", ""),
        lab_index_path=os.getenv("LAB_INDEX_PATH", ""),
    )
