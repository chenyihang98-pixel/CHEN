"""本地 demo 样例 ingest 的 CLI 入口。"""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_agent.pipeline.ingest import ingest_documents


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(description="Ingest synthetic thesis samples into local JSONL artifacts.")
    parser.add_argument("--input", default="data/samples", help="Input directory containing synthetic documents.")
    parser.add_argument(
        "--input-type",
        choices=("auto", "markdown", "pdf"),
        default="auto",
        help="Input document type to ingest.",
    )
    parser.add_argument(
        "--language",
        choices=("auto", "ja", "zh", "en"),
        default="ja",
        help="Document language hint for metadata extraction and processing.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/chunks.jsonl",
        help="Output JSONL path for chunk records.",
    )
    parser.add_argument(
        "--metadata-output",
        default="data/metadata/documents.jsonl",
        help="Output JSONL path for document metadata records.",
    )
    parser.add_argument(
        "--catalog",
        default="",
        help="Optional internal corpus catalog CSV path for preserving lab PDF metadata.",
    )
    return parser


def main() -> None:
    """Run the local ingest pipeline and print summary stats."""
    parser = build_parser()
    args = parser.parse_args()

    stats = ingest_documents(
        input_dir=Path(args.input),
        chunks_output=Path(args.output),
        metadata_output=Path(args.metadata_output),
        input_type=args.input_type,
        language=args.language,
        catalog_path=Path(args.catalog) if args.catalog else None,
    )

    print(f"document_count={stats['document_count']}")
    print(f"chunk_count={stats['chunk_count']}")
    print(f"input_type={stats['input_type']}")
    print(f"language={stats['language']}")
    print(f"chunks_output={stats['chunks_output']}")
    print(f"metadata_output={stats['metadata_output']}")
    if stats.get("catalog_path"):
        print(f"catalog_path={stats['catalog_path']}")


if __name__ == "__main__":
    main()
