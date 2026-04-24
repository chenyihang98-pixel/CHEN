"""内部 PDF 语料 catalog 的稳定管理模块。"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from thesis_agent.corpus.metadata_extractors import extract_internal_pdf_metadata


CATALOG_FIELDS = [
    "doc_id",
    "title",
    "author_name",
    "student_id",
    "advisor_name",
    "year",
    "original_filename",
    "pdf_path",
    "content_hash",
    "status",
]


def _file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_catalog(catalog_path: Path) -> list[dict]:
    """Load a catalog CSV if it exists."""
    if not catalog_path.exists():
        return []

    with catalog_path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def save_catalog(records: list[dict], catalog_path: Path) -> None:
    """Persist catalog records to CSV."""
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with catalog_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CATALOG_FIELDS)
        writer.writeheader()
        for record in records:
            writer.writerow({field: record.get(field, "") for field in CATALOG_FIELDS})


def _next_doc_id(records: list[dict]) -> str:
    max_number = 0
    for record in records:
        doc_id = record.get("doc_id", "")
        if doc_id.startswith("lab_doc_"):
            try:
                max_number = max(max_number, int(doc_id.removeprefix("lab_doc_")))
            except ValueError:
                continue
    return f"lab_doc_{max_number + 1:04d}"


def sync_catalog(
    pdf_root: Path,
    catalog_path: Path,
) -> dict:
    """Scan internal PDFs and update a stable catalog without changing known doc_ids."""
    resolved_root = pdf_root.resolve()
    if not resolved_root.exists():
        raise ValueError(f"PDF root does not exist: {pdf_root}")
    if not resolved_root.is_dir():
        raise ValueError(f"PDF root must be a directory: {pdf_root}")

    existing_records = load_catalog(catalog_path)
    by_hash = {record.get("content_hash", ""): record for record in existing_records if record.get("content_hash")}
    seen_hashes: set[str] = set()

    records = existing_records[:]
    added_count = 0
    updated_count = 0

    for pdf_path in sorted(resolved_root.rglob("*.pdf")):
        if not pdf_path.is_file():
            continue
        content_hash = _file_hash(pdf_path)
        seen_hashes.add(content_hash)
        metadata = extract_internal_pdf_metadata(pdf_path)
        resolved_pdf = pdf_path.resolve().as_posix()

        if content_hash in by_hash:
            record = by_hash[content_hash]
            record.update(
                {
                    "title": metadata.get("title", record.get("title", "")),
                    "author_name": metadata.get("author_name", record.get("author_name", "")),
                    "student_id": metadata.get("student_id", record.get("student_id", "")),
                    "advisor_name": metadata.get("advisor_name", record.get("advisor_name", "")),
                    "year": metadata.get("year", record.get("year", "")),
                    "original_filename": pdf_path.name,
                    "pdf_path": resolved_pdf,
                    "status": "active",
                }
            )
            updated_count += 1
            continue

        record = {
            "doc_id": _next_doc_id(records),
            "title": metadata.get("title", ""),
            "author_name": metadata.get("author_name", ""),
            "student_id": metadata.get("student_id", ""),
            "advisor_name": metadata.get("advisor_name", ""),
            "year": metadata.get("year", ""),
            "original_filename": pdf_path.name,
            "pdf_path": resolved_pdf,
            "content_hash": content_hash,
            "status": "active",
        }
        records.append(record)
        by_hash[content_hash] = record
        added_count += 1

    for record in records:
        if record.get("content_hash") and record["content_hash"] not in seen_hashes:
            record["status"] = "missing"

    save_catalog(records, catalog_path)
    return {
        "pdf_count": len(seen_hashes),
        "catalog_count": len(records),
        "added_count": added_count,
        "updated_count": updated_count,
        "catalog_path": catalog_path.as_posix(),
    }


def catalog_by_doc_id(catalog_path: Path) -> dict[str, dict]:
    """Return active catalog records by doc_id."""
    return {record["doc_id"]: record for record in load_catalog(catalog_path) if record.get("status", "active") == "active"}
