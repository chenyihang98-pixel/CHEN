"""面向检索的本地 tool 模块。"""

from __future__ import annotations

from pathlib import Path

from thesis_agent.pipeline.retrieval import search_tfidf_index
from thesis_agent.privacy.pii import scan_pii
from thesis_agent.tools.schemas import ToolResult


def search_thesis(
    index_path: Path,
    query: str,
    top_k: int = 5,
    allow_pii_query: bool = False,
) -> ToolResult:
    """Search similar thesis chunks from the local TF-IDF index."""
    if not query or not query.strip():
        return ToolResult(
            tool_name="search_thesis",
            ok=False,
            data={},
            errors=["Query must not be empty."],
        )

    pii_findings = scan_pii(query)
    if pii_findings and not allow_pii_query:
        return ToolResult(
            tool_name="search_thesis",
            ok=False,
            data={},
            errors=["PII detected in query. Please remove personal or sensitive information before searching."],
        )

    results = search_tfidf_index(index_path=index_path, query=query, top_k=top_k)
    data = {
        "query": query,
        "top_k": top_k,
        "results": [
            {
                "rank": result.rank,
                "score": round(result.score, 4),
                "title": result.title,
                "citation": result.citation,
                "snippet": result.text[:160].replace("\n", " "),
                "chunk_id": result.chunk_id,
                "doc_id": result.doc_id,
                "author_name": result.metadata.get("author_name", ""),
                "advisor_name": result.metadata.get("advisor_name", ""),
                "year": result.metadata.get("year", ""),
                "pdf_path": result.metadata.get("pdf_path", ""),
                "original_filename": result.metadata.get("original_filename", ""),
                "source_type": result.metadata.get("source_type", ""),
            }
            for result in results
        ],
    }
    return ToolResult(tool_name="search_thesis", ok=True, data=data)
