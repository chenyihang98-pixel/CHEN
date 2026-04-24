"""内部语料 UI 的 PDF 操作辅助模块。"""

from __future__ import annotations

import os
from pathlib import Path


def validate_internal_pdf_path(pdf_path: Path, pdf_root: Path | None = None) -> Path:
    """Validate that a PDF path exists and is under the configured internal root when provided."""
    resolved = pdf_path.resolve()
    if not resolved.exists() or resolved.suffix.lower() != ".pdf":
        raise ValueError("PDF file does not exist or is not a PDF")

    if pdf_root is not None:
        resolved_root = pdf_root.resolve()
        try:
            resolved.relative_to(resolved_root)
        except ValueError as exc:
            raise ValueError("PDF is outside the configured internal PDF root") from exc
    return resolved


def read_pdf_bytes(pdf_path: Path, pdf_root: Path | None = None) -> bytes:
    """Return PDF bytes for a validated internal catalog PDF."""
    safe_path = validate_internal_pdf_path(pdf_path, pdf_root=pdf_root)
    return safe_path.read_bytes()


def pdf_preview_uri(pdf_path: Path, pdf_root: Path | None = None) -> str:
    """Return a browser-loadable URI for previewing a validated local PDF."""
    safe_path = validate_internal_pdf_path(pdf_path, pdf_root=pdf_root)
    return safe_path.as_uri()


def open_pdf(pdf_path: Path, pdf_root: Path | None = None) -> None:
    """Open a validated internal PDF with the local operating system."""
    safe_path = validate_internal_pdf_path(pdf_path, pdf_root=pdf_root)
    if os.name == "nt":
        os.startfile(str(safe_path))  # type: ignore[attr-defined]
        return
    raise RuntimeError("Open PDF is currently implemented for Windows local use only")
