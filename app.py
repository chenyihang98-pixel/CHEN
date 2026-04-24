"""Streamlit MVP UI for the local-only ThesisAgent workflow."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

from thesis_agent import __version__
from thesis_agent.config import get_app_config
from thesis_agent.ui.i18n import get_ui_labels
from thesis_agent.ui.pdf_actions import open_pdf
from thesis_agent.ui.services import (
    build_pdf_action_metadata,
    get_pdf_download_bytes,
    get_demo_asset_status,
    get_internal_asset_status,
    list_demo_samples,
    persist_search_result,
    persist_topic_result,
    rebuild_internal_assets,
    rebuild_demo_assets,
    resolve_doc_id_to_pdf,
    run_search,
    run_structure_check,
    run_topic_analysis,
    set_selected_preview_doc_id,
)


SAMPLES_DIR = Path("data/samples")
CHUNKS_PATH = Path("data/processed/chunks.jsonl")
METADATA_PATH = Path("data/metadata/documents.jsonl")
INDEX_PATH = Path("data/index/tfidf_index.pkl")


def _safe_pdf_filename(item: dict) -> str:
    raw_name = item.get("title") or item.get("original_filename") or item.get("doc_id") or "thesis"
    stem = Path(str(raw_name)).stem
    safe_stem = re.sub(r'[\\/:*?"<>|]+', "_", stem).strip(" ._") or str(item.get("doc_id") or "thesis")
    return f"{safe_stem}.pdf"


def _ui_text(language: str) -> dict[str, str]:
    labels = dict(get_ui_labels(language))
    labels["language"] = language if language in {"ja", "zh", "en"} else "ja"
    return labels


def _render_status(status: dict, labels: dict[str, str]) -> None:
    if status.get("mode"):
        st.write(f"{labels['mode']}: `{status.get('mode')}`")
    st.write(f"{labels['chunks']}: `{str(status.get('chunks_exists', False)).lower()}`")
    st.write(f"{labels['index']}: `{str(status.get('index_exists', False)).lower()}`")
    st.write(f"{labels['chunk_count']}: `{status.get('chunk_count', 0)}`")
    st.write(f"{labels['chunks_path']}: `{status.get('chunks_path', '-')}`")
    st.write(f"{labels['index_path']}: `{status.get('index_path', '-')}`")
    if status.get("catalog_path"):
        st.write(f"{labels['catalog']}: `{status.get('catalog_path')}`")


def _render_home(ui: dict[str, str], status: dict, kb_mode: str) -> None:
    st.subheader(ui["home"])
    overview_key = "local_only_overview_internal" if kb_mode == "internal" else "local_only_overview_demo"
    st.write(ui[overview_key])
    st.warning(ui["privacy"])
    st.info(ui["capabilities"])
    st.caption(ui["plagiarism_note"])
    st.markdown(f"### {ui['demo_asset_readiness']}")
    _render_status(status, ui)


def _show_open_success(message: str) -> None:
    if hasattr(st, "toast"):
        st.toast(message)
    else:  # pragma: no cover - compatibility fallback
        st.success(message)


def _render_pdf_actions(
    item: dict,
    catalog_path: Path | None,
    pdf_root: Path | None,
    key_prefix: str,
    labels: dict[str, str],
) -> None:
    if not catalog_path or not item.get("pdf_path"):
        return

    doc_id = item["doc_id"]
    chunk_id = item.get("chunk_id", "")
    preview_state_key = f"{key_prefix}_preview_bytes_{doc_id}_{chunk_id}"
    columns = st.columns(3)
    with columns[0]:
        if st.button(labels["open_pdf"], key=f"{key_prefix}_open_{doc_id}_{chunk_id}"):
            try:
                pdf_path = resolve_doc_id_to_pdf(catalog_path=catalog_path, doc_id=doc_id, pdf_root=pdf_root)
                open_pdf(pdf_path, pdf_root=pdf_root)
                _show_open_success(labels["open_success"])
            except Exception as exc:  # pragma: no cover - local OS action
                st.error(f"{labels['open_error']} {exc}")
    with columns[1]:
        try:
            pdf_bytes = get_pdf_download_bytes(catalog_path=catalog_path, doc_id=doc_id, pdf_root=pdf_root)
            st.download_button(
                labels["download_pdf"],
                data=pdf_bytes,
                file_name=_safe_pdf_filename(item),
                mime="application/pdf",
                key=f"download_pdf_{key_prefix}_{doc_id}_{chunk_id}",
                on_click="ignore",
            )
        except Exception as exc:
            st.caption(f"{labels['download_unavailable']} {exc}")
    with columns[2]:
        if st.button(labels["preview_pdf"], key=f"{key_prefix}_prepare_preview_{doc_id}_{chunk_id}"):
            try:
                build_pdf_action_metadata(catalog_path=catalog_path, doc_id=doc_id, pdf_root=pdf_root)
                st.session_state[preview_state_key] = get_pdf_download_bytes(
                    catalog_path=catalog_path,
                    doc_id=doc_id,
                    pdf_root=pdf_root,
                )
                set_selected_preview_doc_id(st.session_state, doc_id)
            except Exception as exc:
                st.error(str(exc))
        if st.session_state.get(preview_state_key):
            with st.expander(labels["preview_pdf"], expanded=True):
                st.caption(labels["preview_deferred_message"])
                st.pdf(
                    st.session_state[preview_state_key],
                    height=700,
                    key=f"{key_prefix}_preview_{doc_id}_{chunk_id}",
                )


def _render_internal_metadata(item: dict, labels: dict[str, str]) -> None:
    parts = []
    if item.get("author_name"):
        parts.append(f"{labels['author']}: `{item['author_name']}`")
    if item.get("advisor_name"):
        parts.append(f"{labels['advisor']}: `{item['advisor_name']}`")
    if item.get("year"):
        parts.append(f"{labels['year']}: `{item['year']}`")
    if parts:
        st.write(" | ".join(parts))


def _render_search_tab(
    ui: dict[str, str],
    index_path: Path,
    top_k: int,
    kb_mode: str = "demo",
    catalog_path: Path | None = None,
    pdf_root: Path | None = None,
) -> None:
    labels = get_ui_labels(ui.get("language", "ja"))
    st.subheader(ui["search"])
    with st.form("search_form"):
        query = st.text_input(
            ui["search_input"],
            value=st.session_state.get("last_search_query", ""),
            key="search_query",
        )
        submitted = st.form_submit_button(ui["search_button"])
    if submitted:
        result = run_search(
            index_path=index_path,
            query=query,
            top_k=top_k,
            kb_mode=kb_mode,
            catalog_path=catalog_path,
        )
        persist_search_result(st.session_state, query, result)
        if not result["ok"]:
            for error in result["errors"]:
                st.error(error)

    persisted = st.session_state.get("last_search_results")
    if not persisted:
        return

    if not persisted["ok"]:
        for error in persisted["errors"]:
            st.error(error)
        return

    if not persisted["results"]:
        st.info(labels["no_results"])
        return

    st.markdown(f"### {labels['search_results']}")
    for item in persisted["results"]:
        st.markdown(f"**{item['rank']}. {item['title']}**")
        st.write(f"{labels['score']}: `{item['score']:.4f}`")
        st.write(f"{labels['citation']}: `{item['citation']}`")
        if item.get("matched_chunk_count"):
            st.write(f"{labels['matched_chunk_count']}: `{item['matched_chunk_count']}`")
            if item.get("matched_chunks"):
                with st.expander(labels["matched_chunks"]):
                    for chunk in item["matched_chunks"]:
                        st.write(f"{chunk.get('citation', '')} | {labels['score']}: `{float(chunk.get('score', 0.0)):.4f}`")
                        st.write(chunk.get("snippet", ""))
        if kb_mode == "internal":
            _render_internal_metadata(item, labels)
            _render_pdf_actions(item, catalog_path=catalog_path, pdf_root=pdf_root, key_prefix="search", labels=labels)
        st.write(item["snippet"])
        st.divider()


def _render_topic_tab(
    ui: dict[str, str],
    index_path: Path,
    top_k: int,
    language: str,
    kb_mode: str = "demo",
    catalog_path: Path | None = None,
    pdf_root: Path | None = None,
) -> None:
    labels = get_ui_labels(ui.get("language", "ja"))
    st.subheader(ui["topic"])
    with st.form("topic_form"):
        topic = st.text_input(ui["topic_input"], value=st.session_state.get("last_topic", ""), key="topic_input")
        submitted = st.form_submit_button(ui["topic_button"])
    if submitted:
        result = run_topic_analysis(
            index_path=index_path,
            topic=topic,
            top_k=top_k,
            language=language,
            kb_mode=kb_mode,
            catalog_path=catalog_path,
        )
        persist_topic_result(st.session_state, topic, result)
        if not result["ok"]:
            for error in result["errors"]:
                st.error(error)

    result = st.session_state.get("last_topic_analysis")
    if not result:
        return

    if not result["ok"]:
        for error in result["errors"]:
            st.error(error)
        return

    st.write(f"{labels['risk_level']}: `{result['risk_level']}`")
    st.write(f"{labels['risk_score']}: `{result['risk_score']:.4f}`")
    st.write(f"{labels['result_count']}: `{result['result_count']}`")
    st.write(f"{labels['citations']}:")
    for citation in result["citations"]:
        st.write(f"- `{citation}`")
    if kb_mode == "internal" and result.get("references"):
        st.markdown(f"### {labels['pdf_references']}")
        for item in result["references"]:
            st.markdown(f"**{item['title']}**")
            _render_internal_metadata(item, labels)
            st.write(f"{labels['citation']}: `{item['citation']}`")
            if item.get("matched_chunk_count"):
                st.write(f"{labels['matched_chunk_count']}: `{item['matched_chunk_count']}`")
            _render_pdf_actions(item, catalog_path=catalog_path, pdf_root=pdf_root, key_prefix="topic", labels=labels)
    if result.get("note"):
        st.caption(result["note"])
    st.markdown(result["report_markdown"])
    st.download_button(
        label=ui["report_download"],
        data=result["report_markdown"],
        file_name="topic_report.md",
        mime="text/markdown",
        key="topic_report_download",
        on_click="ignore",
    )


def _render_structure_tab(ui: dict[str, str], samples_dir: Path, language: str) -> None:
    labels = get_ui_labels(ui.get("language", "ja"))
    st.subheader(ui["structure"])
    sample_files = list_demo_samples(samples_dir)
    if not sample_files:
        st.info(labels["no_synthetic_samples"])
        return

    selected_sample = st.selectbox(ui["structure_input"], options=sample_files, index=0)

    if st.button(ui["structure_button"], key="structure_button"):
        if not selected_sample:
            st.error(labels["no_synthetic_sample_selected"])
            return

        result = run_structure_check(sample_path=samples_dir / selected_sample, language=language)
        if not result["ok"]:
            for error in result["errors"]:
                st.error(error)
            return

        st.write(f"{labels['score']}: `{result['score']:.4f}`")
        st.write(f"{labels['language']}: `{result['language']}`")
        st.write(f"{labels['present_sections']}:")
        for section in result["present_sections"]:
            st.write(f"- {section}")
        st.write(f"{labels['missing_sections']}:")
        if result["missing_sections"]:
            for section in result["missing_sections"]:
                st.write(f"- {section}")
        else:
            st.write(f"- {labels['none']}")
        st.write(f"{labels['suggestions']}:")
        for suggestion in result["suggestions"]:
            st.write(f"- {suggestion}")


def main() -> None:
    """Render the Stage 5 local-only Streamlit MVP."""
    config = get_app_config()
    kb_mode = config.kb_mode
    initial_ui_language = config.ui_language if config.ui_language in {"ja", "zh", "en"} else "ja"
    ui = _ui_text(initial_ui_language)

    st.set_page_config(page_title="ThesisAgent", page_icon="TA", layout="wide")
    st.title(ui["app_title"])
    st.caption(f"Version {__version__} | {ui['stage_caption']}")

    selected_language = st.sidebar.selectbox(
        ui["language"],
        options=("ja", "zh", "en", "auto"),
        index=0,
    )
    effective_ui_language = selected_language if selected_language in {"ja", "zh", "en"} else initial_ui_language
    ui = _ui_text(effective_ui_language)
    top_k = st.sidebar.slider(ui["top_k"], min_value=1, max_value=10, value=5)

    st.sidebar.subheader(ui["sidebar_title"])
    st.sidebar.info(ui["local_notice"])
    show_debug_timing = st.sidebar.checkbox(ui["debug_timing"], value=False)

    if kb_mode == "internal":
        active_index_path = Path(config.lab_index_path or "data/index/tfidf_index.pkl")
        active_catalog_path = Path(config.lab_catalog_path) if config.lab_catalog_path else None
        active_pdf_root = Path(config.lab_pdf_root) if config.lab_pdf_root else None
        active_chunks_path = Path(config.lab_chunks_path or "data/processed/chunks.jsonl")
    else:
        active_index_path = INDEX_PATH
        active_catalog_path = None
        active_pdf_root = None
        active_chunks_path = CHUNKS_PATH

    try:
        if kb_mode == "internal":
            if active_catalog_path is None or active_pdf_root is None:
                raise ValueError(ui["internal_mode_requires_paths"])
            status = get_internal_asset_status(
                catalog_path=active_catalog_path,
                chunks_path=active_chunks_path,
                index_path=active_index_path,
            )
        else:
            status = get_demo_asset_status(
                chunks_path=CHUNKS_PATH,
                metadata_path=METADATA_PATH,
                index_path=INDEX_PATH,
            )
    except Exception as exc:  # pragma: no cover - Streamlit presentation guard
        status = {
            "mode": kb_mode,
            "chunks_exists": False,
            "index_exists": False,
            "chunk_count": 0,
            "chunks_path": active_chunks_path.name,
            "index_path": active_index_path.name,
            "metadata_path": METADATA_PATH.as_posix(),
        }
        st.sidebar.error(str(exc))

    if st.sidebar.button(ui["rebuild_button"]):
        try:
            if kb_mode == "internal":
                if active_catalog_path is None or active_pdf_root is None:
                    raise ValueError(ui["internal_mode_requires_paths"])
                status = rebuild_internal_assets(
                    pdf_root=active_pdf_root,
                    catalog_path=active_catalog_path,
                    chunks_path=active_chunks_path,
                    index_path=active_index_path,
                    language=selected_language,
                )
            else:
                status = rebuild_demo_assets(
                    samples_dir=SAMPLES_DIR,
                    chunks_path=CHUNKS_PATH,
                    metadata_path=METADATA_PATH,
                    index_path=INDEX_PATH,
                    language=selected_language,
                )
            st.sidebar.success(ui["demo_assets_ready"])
        except Exception as exc:  # pragma: no cover - Streamlit presentation guard
            st.sidebar.error(str(exc))

    st.sidebar.markdown(f"### {ui['status_title']}")
    _render_status(status, ui)
    if show_debug_timing:
        search_timing = st.session_state.get("last_search_results", {}).get("timing", {})
        topic_timing = st.session_state.get("last_topic_analysis", {}).get("timing", {})
        if search_timing.get("search_seconds") is not None:
            st.sidebar.write(f"{ui['search_seconds']}: `{search_timing['search_seconds']}`")
        if topic_timing.get("topic_seconds") is not None:
            st.sidebar.write(f"{ui['topic_seconds']}: `{topic_timing['topic_seconds']}`")

    tabs = st.tabs([ui["home"], ui["search"], ui["topic"], ui["structure"]])
    with tabs[0]:
        _render_home(ui, status, kb_mode)
    with tabs[1]:
        _render_search_tab(
            ui,
            active_index_path,
            top_k,
            kb_mode=kb_mode,
            catalog_path=active_catalog_path,
            pdf_root=active_pdf_root,
        )
    with tabs[2]:
        _render_topic_tab(
            ui,
            active_index_path,
            top_k,
            selected_language,
            kb_mode=kb_mode,
            catalog_path=active_catalog_path,
            pdf_root=active_pdf_root,
        )
    with tabs[3]:
        _render_structure_tab(ui, SAMPLES_DIR, selected_language)


if __name__ == "__main__":
    main()
