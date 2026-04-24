"""检索本地 TF-IDF 索引的 CLI。"""

from __future__ import annotations

import argparse
from pathlib import Path

from thesis_agent.pipeline.retrieval import search_tfidf_index


def build_parser() -> argparse.ArgumentParser:
    """Build the search CLI argument parser."""
    parser = argparse.ArgumentParser(description="Search a local TF-IDF retrieval index.")
    parser.add_argument("--index", default="data/index/tfidf_index.pkl", help="Path to the TF-IDF index file.")
    parser.add_argument("--query", required=True, help="Search query text.")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to return.")
    return parser


def main() -> None:
    """Run a local TF-IDF search and print ranked results."""
    parser = build_parser()
    args = parser.parse_args()

    results = search_tfidf_index(index_path=Path(args.index), query=args.query, top_k=args.top_k)

    for result in results:
        snippet = result.text[:120].replace("\n", " ")
        print(f"rank={result.rank}")
        print(f"score={result.score:.4f}")
        print(f"title={result.title}")
        print(f"citation={result.citation}")
        print(f"snippet={snippet}")
        print("---")


if __name__ == "__main__":
    main()
