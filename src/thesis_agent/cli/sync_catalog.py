"""同步内部 PDF catalog 的 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_agent.corpus.catalog import sync_catalog


def build_parser() -> argparse.ArgumentParser:
    """Build the catalog sync CLI parser."""
    parser = argparse.ArgumentParser(description="Synchronize an internal text-based PDF catalog.")
    parser.add_argument("--pdf-root", required=True, help="External directory containing internal thesis PDFs.")
    parser.add_argument("--catalog", required=True, help="Output catalog CSV path.")
    return parser


def main() -> None:
    """Synchronize catalog and print summary stats."""
    parser = build_parser()
    args = parser.parse_args()

    stats = sync_catalog(pdf_root=Path(args.pdf_root), catalog_path=Path(args.catalog))
    print(f"pdf_count={stats['pdf_count']}")
    print(f"catalog_count={stats['catalog_count']}")
    print(f"added_count={stats['added_count']}")
    print(f"updated_count={stats['updated_count']}")
    print(f"catalog_path={stats['catalog_path']}")


if __name__ == "__main__":
    main()
