"""Service helpers for the local Streamlit MVP."""

from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st

from thesis_agent.corpus.catalog import catalog_by_doc_id, load_catalog, sync_catalog
from thesis_agent.llm.mock import MockLLM
from thesis_agent.pipeline.ingest import ingest_documents
from thesis_agent.pipeline.retrieval import build_tfidf_index
from thesis_agent.privacy.pii import scan_pii
from thesis_agent.retrieval.io import load_chunks_jsonl
from thesis_agent.retrieval.models import SearchResult
from thesis_agent.retrieval.tfidf import TfidfRetriever
from thesis_agent.tools.schemas import ToolResult
from thesis_agent.tools.structure import analyze_structure_file
from thesis_agent.tools.topic import _build_recommendations
from thesis_agent.ui.pdf_actions import pdf_preview_uri, read_pdf_bytes


WORKSPACE_ROOT = Path.cwd().resolve()
FORBIDDEN_PARTS = {"raw", "private", "anonymized"}


def _validate_workspace_path(path: Path) -> Path:
    resolved = path.resolve()
    try:
        resolved.relative_to(WORKSPACE_ROOT)
    except ValueError as exc:
        raise ValueError("Refusing to access files outside the project workspace") from exc

    if any(part.lower() in FORBIDDEN_PARTS for part in resolved.parts):
        raise ValueError("Refusing to access a forbidden private data directory")
    return resolved


def _display_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(WORKSPACE_ROOT).as_posix()
    except ValueError:
        return path.name


def _display_internal_path(path: Path) -> str:
    """Avoid showing absolute internal PDF paths in user-facing UI state."""
    return path.name


def _file_mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0.0


@st.cache_resource(show_spinner=False)
def load_cached_index(index_path: str, index_mtime: float) -> TfidfRetriever:
    """Load a TF-IDF retriever, invalidating the cache when the index file changes."""
    del index_mtime
    return TfidfRetriever.load(Path(index_path))


@st.cache_data(show_spinner=False)
def load_cached_catalog(catalog_path: str, catalog_mtime: float) -> list[dict]:
    """Load catalog rows, invalidating the cache when the CSV changes."""
    del catalog_mtime
    return load_catalog(Path(catalog_path))


@st.cache_data(show_spinner=False)
def load_cached_documents(metadata_path: str, metadata_mtime: float) -> list[dict]:
    """Load document metadata JSONL, invalidating the cache when the file changes."""
    del metadata_mtime
    path = Path(metadata_path)
    if not path.exists():
        return []
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                records.append(json.loads(stripped))
    return records


@st.cache_data(show_spinner=False)
def load_cached_sample_names(samples_dir: str, samples_mtime: float) -> list[str]:
    """Load synthetic sample names, invalidating when the samples directory changes."""
    del samples_mtime
    path = Path(samples_dir)
    if not path.exists():
        return []
    return sorted(item.name for item in path.iterdir() if item.is_file() and item.suffix.lower() == ".md")


def _chunk_count_from_jsonl(chunks_path: Path) -> int:
    if not chunks_path.exists():
        return 0
    return len(load_chunks_jsonl(chunks_path))


def get_demo_asset_status(
    chunks_path: Path,
    metadata_path: Path,
    index_path: Path,
) -> dict:
    """Return cheap demo asset status without rebuilding or scanning raw documents."""
    safe_chunks_path = _validate_workspace_path(chunks_path)
    safe_metadata_path = _validate_workspace_path(metadata_path)
    safe_index_path = _validate_workspace_path(index_path)
    return {
        "mode": "demo",
        "chunks_exists": safe_chunks_path.exists(),
        "index_exists": safe_index_path.exists(),
        "metadata_exists": safe_metadata_path.exists(),
        "chunk_count": _chunk_count_from_jsonl(safe_chunks_path),
        "index_path": _display_path(safe_index_path),
        "chunks_path": _display_path(safe_chunks_path),
        "metadata_path": _display_path(safe_metadata_path),
    }


def get_internal_asset_status(
    catalog_path: Path,
    chunks_path: Path,
    index_path: Path,
) -> dict:
    """Return cheap internal asset status without syncing, ingesting, indexing, or scanning PDFs."""
    return {
        "mode": "internal",
        "catalog_exists": catalog_path.exists(),
        "chunks_exists": chunks_path.exists(),
        "index_exists": index_path.exists(),
        "chunk_count": _chunk_count_from_jsonl(chunks_path) if chunks_path.exists() else 0,
        "catalog_count": len(load_cached_catalog(str(catalog_path), _file_mtime(catalog_path)))
        if catalog_path.exists()
        else 0,
        "index_path": _display_internal_path(index_path),
        "chunks_path": _display_internal_path(chunks_path),
        "catalog_path": _display_internal_path(catalog_path),
    }


def rebuild_demo_assets(
    samples_dir: Path,
    chunks_path: Path,
    metadata_path: Path,
    index_path: Path,
    language: str = "ja",
) -> dict:
    """Rebuild synthetic demo assets from local sample files."""
    safe_samples_dir = _validate_workspace_path(samples_dir)
    safe_chunks_path = _validate_workspace_path(chunks_path)
    safe_metadata_path = _validate_workspace_path(metadata_path)
    safe_index_path = _validate_workspace_path(index_path)

    ingest_documents(
        input_dir=safe_samples_dir,
        chunks_output=safe_chunks_path,
        metadata_output=safe_metadata_path,
        input_type="markdown",
        language=language,
    )
    build_tfidf_index(
        chunks_path=safe_chunks_path,
        index_output=safe_index_path,
        language=language,
    )

    return get_demo_asset_status(
        chunks_path=safe_chunks_path,
        metadata_path=safe_metadata_path,
        index_path=safe_index_path,
    )


def ensure_demo_assets(
    samples_dir: Path,
    chunks_path: Path,
    metadata_path: Path,
    index_path: Path,
    language: str = "ja",
) -> dict:
    """Backward-compatible demo helper that rebuilds only when assets are missing."""
    safe_samples_dir = _validate_workspace_path(samples_dir)
    status = get_demo_asset_status(chunks_path=chunks_path, metadata_path=metadata_path, index_path=index_path)
    if not status["chunks_exists"] or not status["index_exists"]:
        return rebuild_demo_assets(
            samples_dir=safe_samples_dir,
            chunks_path=chunks_path,
            metadata_path=metadata_path,
            index_path=index_path,
            language=language,
        )
    return status


def rebuild_internal_assets(
    pdf_root: Path,
    catalog_path: Path,
    chunks_path: Path,
    index_path: Path,
    language: str = "ja",
) -> dict:
    """Explicitly rebuild internal catalog, chunks, and index from a configured PDF root."""
    if not pdf_root:
        raise ValueError("Internal mode requires LAB_PDF_ROOT")

    sync_catalog(pdf_root=pdf_root, catalog_path=catalog_path)
    ingest_documents(
        input_dir=pdf_root,
        chunks_output=chunks_path,
        metadata_output=chunks_path.with_name("documents.jsonl"),
        input_type="pdf",
        language=language,
        catalog_path=catalog_path,
    )
    build_tfidf_index(chunks_path=chunks_path, index_output=index_path, language=language)
    return get_internal_asset_status(catalog_path=catalog_path, chunks_path=chunks_path, index_path=index_path)


def ensure_internal_assets(
    pdf_root: Path,
    catalog_path: Path,
    chunks_path: Path,
    index_path: Path,
    language: str = "ja",
) -> dict:
    """Backward-compatible internal helper; explicit rebuild only when required by old callers."""
    status = get_internal_asset_status(catalog_path=catalog_path, chunks_path=chunks_path, index_path=index_path)
    if not status["catalog_exists"] or not status["chunks_exists"] or not status["index_exists"]:
        return rebuild_internal_assets(
            pdf_root=pdf_root,
            catalog_path=catalog_path,
            chunks_path=chunks_path,
            index_path=index_path,
            language=language,
        )
    return status


def load_internal_catalog(catalog_path: Path) -> list[dict]:
    """Load active internal catalog records for UI display."""
    records = load_cached_catalog(str(catalog_path), _file_mtime(catalog_path))
    return [record for record in records if record.get("status", "active") == "active"]


def _catalog_lookup(catalog_path: Path | None) -> dict[str, dict]:
    if catalog_path is None or not catalog_path.exists():
        return {}
    records = load_cached_catalog(str(catalog_path), _file_mtime(catalog_path))
    return {record["doc_id"]: record for record in records if record.get("status", "active") == "active"}


def _documents_lookup(metadata_path: Path | None) -> dict[str, dict]:
    if metadata_path is None or not metadata_path.exists():
        return {}
    records = load_cached_documents(str(metadata_path), _file_mtime(metadata_path))
    return {record["doc_id"]: record for record in records if record.get("doc_id")}


def resolve_doc_id_to_pdf(
    catalog_path: Path,
    doc_id: str,
    pdf_root: Path | None = None,
) -> Path:
    """Resolve an internal doc_id to a catalog PDF path."""
    record = _catalog_lookup(catalog_path).get(doc_id) or catalog_by_doc_id(catalog_path).get(doc_id)
    if not record:
        raise ValueError(f"Unknown internal doc_id: {doc_id}")
    pdf_path = Path(record["pdf_path"]).resolve()
    if pdf_root is not None:
        try:
            pdf_path.relative_to(pdf_root.resolve())
        except ValueError as exc:
            raise ValueError("Resolved PDF is outside the configured internal PDF root") from exc
    return pdf_path


def get_pdf_download_bytes(
    catalog_path: Path,
    doc_id: str,
    pdf_root: Path | None = None,
) -> bytes:
    """Return bytes for a catalog-validated internal PDF."""
    pdf_path = resolve_doc_id_to_pdf(catalog_path=catalog_path, doc_id=doc_id, pdf_root=pdf_root)
    return read_pdf_bytes(pdf_path=pdf_path, pdf_root=pdf_root)


def build_pdf_action_metadata(
    catalog_path: Path,
    doc_id: str,
    pdf_root: Path | None = None,
) -> dict:
    """Return validated PDF action metadata without exposing raw paths as labels."""
    pdf_path = resolve_doc_id_to_pdf(catalog_path=catalog_path, doc_id=doc_id, pdf_root=pdf_root)
    return {
        "doc_id": doc_id,
        "file_name": f"{doc_id}.pdf",
        "preview_uri": pdf_preview_uri(pdf_path=pdf_path, pdf_root=pdf_root),
        "can_open": True,
        "can_download": True,
    }


def persist_search_result(state: dict, query: str, result: dict) -> None:
    """Persist search UI state across Streamlit reruns."""
    state["last_search_query"] = query
    state["last_search_results"] = result


def persist_topic_result(state: dict, topic: str, result: dict) -> None:
    """Persist topic UI state across Streamlit reruns."""
    state["last_topic"] = topic
    state["last_topic_analysis"] = result
    state["last_topic_report"] = result.get("report_markdown", "")


def set_selected_preview_doc_id(state: dict, doc_id: str) -> None:
    """Persist the selected PDF preview doc_id."""
    state["selected_preview_doc_id"] = doc_id


def list_demo_samples(samples_dir: Path) -> list[str]:
    """Return sorted synthetic sample filenames from a safe local directory."""
    safe_samples_dir = _validate_workspace_path(samples_dir)
    if not safe_samples_dir.exists():
        return []
    return load_cached_sample_names(str(safe_samples_dir), _file_mtime(safe_samples_dir))


def _format_search_result(result: SearchResult, catalog_record: dict | None = None, document_record: dict | None = None) -> dict:
    metadata = dict(result.metadata)
    if document_record:
        metadata.update({key: value for key, value in document_record.items() if value})
    if catalog_record:
        metadata.update({key: value for key, value in catalog_record.items() if value})
    return {
        "rank": result.rank,
        "score": round(result.score, 4),
        "title": metadata.get("title") or result.title,
        "citation": result.citation,
        "snippet": result.text[:160].replace("\n", " "),
        "chunk_id": result.chunk_id,
        "doc_id": result.doc_id,
        "author_name": metadata.get("author_name", ""),
        "advisor_name": metadata.get("advisor_name", ""),
        "year": metadata.get("year", ""),
        "pdf_path": metadata.get("pdf_path", ""),
        "original_filename": metadata.get("original_filename", ""),
        "source_type": metadata.get("source_type", ""),
    }


def dedupe_results_by_doc_id(results: list[dict], top_k: int) -> list[dict]:
    """Collapse chunk-level hits into document-level search results."""
    best_by_doc_id: dict[str, dict] = {}
    matched_chunks_by_doc_id: dict[str, list[dict]] = {}

    for result in results:
        doc_id = result.get("doc_id", "")
        if not doc_id:
            continue

        chunk_summary = {
            "rank": result.get("rank"),
            "score": result.get("score", 0.0),
            "citation": result.get("citation", ""),
            "chunk_id": result.get("chunk_id", ""),
            "snippet": result.get("snippet", ""),
        }
        matched_chunks_by_doc_id.setdefault(doc_id, []).append(chunk_summary)

        current_best = best_by_doc_id.get(doc_id)
        if current_best is None or float(result.get("score", 0.0)) > float(current_best.get("score", 0.0)):
            best_by_doc_id[doc_id] = dict(result)

    deduped = sorted(best_by_doc_id.values(), key=lambda item: float(item.get("score", 0.0)), reverse=True)
    deduped = deduped[: max(top_k, 0)]
    for index, result in enumerate(deduped, start=1):
        doc_id = result["doc_id"]
        matched_chunks = sorted(
            matched_chunks_by_doc_id.get(doc_id, []),
            key=lambda item: float(item.get("score", 0.0)),
            reverse=True,
        )
        result["rank"] = index
        result["matched_chunk_count"] = len(matched_chunks)
        result["matched_chunks"] = matched_chunks
    return deduped


def _search_cached_index(
    index_path: Path,
    query: str,
    top_k: int,
    catalog_path: Path | None = None,
    metadata_path: Path | None = None,
) -> tuple[list[dict], float]:
    start = time.perf_counter()
    retriever = load_cached_index(str(index_path), _file_mtime(index_path))
    catalog = _catalog_lookup(catalog_path)
    documents = _documents_lookup(metadata_path)
    candidate_k = max(top_k * 5, top_k)
    raw_results = retriever.search(query=query, top_k=candidate_k)
    results = [
        _format_search_result(
            result,
            catalog_record=catalog.get(result.doc_id),
            document_record=documents.get(result.doc_id),
        )
        for result in raw_results
    ]
    return dedupe_results_by_doc_id(results, top_k=top_k), time.perf_counter() - start


def run_search(
    index_path: Path,
    query: str,
    top_k: int = 5,
    kb_mode: str = "demo",
    catalog_path: Path | None = None,
    metadata_path: Path | None = None,
) -> dict:
    """Run local search and normalize the result for Streamlit rendering."""
    if not query or not query.strip():
        return {"ok": False, "errors": ["Query must not be empty."], "warnings": [], "query": query, "results": []}

    pii_findings = scan_pii(query)
    if pii_findings and kb_mode != "internal":
        return {
            "ok": False,
            "errors": ["PII detected in query. Please remove personal or sensitive information before searching."],
            "warnings": [],
            "query": query,
            "results": [],
        }

    safe_index_path = _validate_workspace_path(index_path) if kb_mode == "demo" else index_path
    try:
        results, elapsed = _search_cached_index(
            index_path=safe_index_path,
            query=query,
            top_k=top_k,
            catalog_path=catalog_path if kb_mode == "internal" else None,
            metadata_path=metadata_path,
        )
    except Exception as exc:
        return {"ok": False, "errors": [str(exc)], "warnings": [], "query": query, "results": []}
    return {
        "ok": True,
        "errors": [],
        "warnings": [],
        "query": query,
        "results": results,
        "timing": {"search_seconds": round(elapsed, 4)},
    }


def _compare_topic_from_results(topic: str, results: list[dict]) -> ToolResult:
    top_score = float(results[0]["score"]) if results else 0.0
    if top_score >= 0.18:
        risk_level = "high"
    elif top_score >= 0.07:
        risk_level = "medium"
    else:
        risk_level = "low"
    return ToolResult(
        tool_name="compare_topic",
        ok=True,
        data={
            "topic": topic,
            "risk_level": risk_level,
            "risk_score": round(top_score, 4),
            "top_similarity_score": round(top_score, 4),
            "similar_count": len(results),
            "citations": [result["citation"] for result in results],
            "recommendations": _build_recommendations(risk_level),
            "references": results,
            "note": "This is only a topic similarity / overlap signal, not plagiarism detection.",
        },
    )


def run_topic_analysis(
    index_path: Path,
    topic: str,
    top_k: int = 5,
    language: str = "ja",
    kb_mode: str = "demo",
    catalog_path: Path | None = None,
    metadata_path: Path | None = None,
) -> dict:
    """Run deterministic topic analysis and local MockLLM report generation."""
    start = time.perf_counter()
    search_result = run_search(
        index_path=index_path,
        query=topic,
        top_k=top_k,
        kb_mode=kb_mode,
        catalog_path=catalog_path,
        metadata_path=metadata_path,
    )
    if not search_result["ok"]:
        return {
            "ok": False,
            "errors": search_result["errors"],
            "warnings": search_result["warnings"],
            "risk_level": "",
            "risk_score": 0.0,
            "citations": [],
            "report_markdown": "",
            "result_count": 0,
        }

    topic_result = _compare_topic_from_results(topic, search_result["results"])
    report_markdown = MockLLM().generate_topic_report(
        topic=topic,
        topic_analysis=topic_result.data,
        search_results=search_result["results"],
        language=language,
    )

    return {
        "ok": True,
        "errors": [],
        "warnings": topic_result.warnings,
        "risk_level": topic_result.data["risk_level"],
        "risk_score": topic_result.data["risk_score"],
        "citations": topic_result.data["citations"],
        "references": topic_result.data.get("references", []),
        "report_markdown": report_markdown,
        "result_count": len(search_result["results"]),
        "note": topic_result.data.get("note", ""),
        "timing": {
            "topic_seconds": round(time.perf_counter() - start, 4),
            **search_result.get("timing", {}),
        },
    }


def run_structure_check(
    sample_path: Path,
    language: str = "ja",
) -> dict:
    """Run local structure analysis on a safe synthetic sample file."""
    safe_sample_path = _validate_workspace_path(sample_path)
    result = analyze_structure_file(path=safe_sample_path, language=language)
    return {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "score": result.data.get("score", 0.0),
        "language": result.data.get("language", language),
        "present_sections": result.data.get("present_sections", []),
        "missing_sections": result.data.get("missing_sections", []),
        "suggestions": result.data.get("suggestions", []),
        "sample_name": safe_sample_path.name,
    }
