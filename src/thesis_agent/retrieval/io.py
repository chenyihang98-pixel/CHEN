"""本地检索 artifacts 的 I/O 辅助模块。"""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_CHUNK_FIELDS = {"chunk_id", "doc_id", "title", "text", "metadata"}


def load_chunks_jsonl(path: Path) -> list[dict]:
    """Load chunk records from a JSONL file."""
    if not path.exists():
        raise ValueError(f"Chunks file does not exist: {path}")

    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            missing = REQUIRED_CHUNK_FIELDS - set(record.keys())
            if missing:
                missing_list = ", ".join(sorted(missing))
                raise ValueError(f"Missing required fields at line {line_number}: {missing_list}")
            if not isinstance(record["metadata"], dict):
                raise ValueError(f"Field 'metadata' must be a dict at line {line_number}")
            records.append(record)

    if not records:
        raise ValueError("No chunks found in JSONL file")

    return records


def save_jsonl(records: list[dict], path: Path) -> None:
    """Write records to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
